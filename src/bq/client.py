"""BigQuery Live Client wrapper with read-only safety guardrails and table qualification.

Adheres to Invariant 1 (2-Minute Evaluator Rule with handled credentials) and
Invariant 6 (Table Qualification Sanitizer).
"""

import logging
import os
import re
from typing import Any

import google.auth
import pandas as pd
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from google.cloud import bigquery
from rich.console import Console

from src.bq.exceptions import (
    BigQueryClientError,
    CredentialsMissingError,
    ReadOnlyQueryViolationError,
)
from src.bq.schema import (
    DEFAULT_DATASET,
    SchemaInspector,
    sanitize_table_qualification,
)

logger = logging.getLogger(__name__)

# Mutating SQL keywords that violate read-only safety
MUTATING_KEYWORDS = (
    r"\bINSERT\s+INTO\b",
    r"\bUPDATE\b",
    r"\bDELETE\s+FROM\b",
    r"\bDROP\s+TABLE\b",
    r"\bDROP\s+VIEW\b",
    r"\bALTER\s+TABLE\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bCREATE\s+TABLE\b",
    r"\bCREATE\s+VIEW\b",
    r"\bCREATE\s+OR\s+REPLACE\b",
    r"\bMERGE\s+INTO\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
)


def is_read_only_query(sql: str) -> bool:
    """Validate whether an arbitrary SQL string is strictly read-only.

    Edge cases handled:
    - Strips single-line (`--`) and multi-line (`/* */`) comments before scanning.
    - Rejects multi-statement chaining via semicolons (e.g. `SELECT 1; DROP TABLE orders;`).
    - Enforces that the statement must begin with SELECT or WITH.
    - Rejects any mutating keywords with word boundaries.
    """
    if not sql or not sql.strip():
        return False

    # 1. Strip comments
    # Strip multi-line comments
    cleaned = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    # Strip single-line comments
    cleaned = re.sub(r"--.*?$", " ", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    if not cleaned:
        return False

    # 2. Reject multi-statement queries (semicolon followed by non-whitespace)
    if re.search(r";\s*\S", cleaned):
        return False

    # Remove trailing semicolon if present
    cleaned = cleaned.rstrip(";").strip()

    # 3. Must begin with SELECT or WITH
    if not re.match(r"(?i)^(SELECT|WITH)\b", cleaned):
        return False

    # 4. Forbid any mutating keywords
    for pattern in MUTATING_KEYWORDS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            return False

    return True


class BigQueryClient:
    """Production BigQuery client wrapper with automated table qualification and read-only validation."""

    def __init__(
        self,
        project_id: str | None = None,
        dataset_id: str | None = DEFAULT_DATASET,
        client: bigquery.Client | None = None,
    ) -> None:
        """Initialize the BigQuery client.

        Raises:
            CredentialsMissingError: If Google Cloud ADC cannot be discovered,
                                     allowing seamless fallback to DuckDB.
        """
        self.dataset_id = (dataset_id or DEFAULT_DATASET).strip("`")
        self.project_id = project_id

        if client is not None:
            self.client = client
        else:
            try:
                credentials, discovered_project = google.auth.default()
                active_project = project_id or discovered_project
                self.client = bigquery.Client(
                    project=active_project,
                    credentials=credentials,
                )
            except (OSError, DefaultCredentialsError, GoogleAuthError) as e:
                raise CredentialsMissingError(
                    f"Google Cloud Application Default Credentials (ADC) missing or invalid: {e}. "
                    "Use MockBigQueryEngine or configure gcloud auth application-default login."
                ) from e
            except Exception as e:
                raise BigQueryClientError(f"Failed to initialize BigQuery client: {e}") from e

        self.schema_inspector = SchemaInspector(
            client=self.client,
            dataset_id=self.dataset_id,
        )

    def execute_query(
        self,
        sql: str,
        sanitize: bool = True,
    ) -> bigquery.table.RowIterator:
        """Execute GoogleSQL query with validation and qualification."""
        if not is_read_only_query(sql):
            raise ReadOnlyQueryViolationError(
                f"Query rejected: Only read-only SELECT and WITH statements are permitted. Query: {sql[:100]}"
            )

        target_sql = sanitize_table_qualification(sql, self.dataset_id) if sanitize else sql
        logger.debug(f"Executing BigQuery SQL: {target_sql}")

        try:
            query_job = self.client.query(target_sql)
            return query_job.result()
        except Exception as e:
            raise BigQueryClientError(f"BigQuery execution failed: {e}") from e

    def query_to_dataframe(
        self,
        sql: str,
        sanitize: bool = True,
    ) -> pd.DataFrame:
        """Execute read-only SQL query and return results as a Pandas DataFrame."""
        if not is_read_only_query(sql):
            raise ReadOnlyQueryViolationError(
                f"Query rejected: Only read-only SELECT and WITH statements are permitted. Query: {sql[:100]}"
            )

        target_sql = sanitize_table_qualification(sql, self.dataset_id) if sanitize else sql
        logger.debug(f"Executing BigQuery to DataFrame: {target_sql}")

        try:
            query_job = self.client.query(target_sql)
            return query_job.to_dataframe()
        except Exception as e:
            raise BigQueryClientError(f"BigQuery query to dataframe failed: {e}") from e

    def query_to_dicts(
        self,
        sql: str,
        sanitize: bool = True,
    ) -> list[dict[str, Any]]:
        """Execute read-only SQL and return list of row dictionaries for LangGraph AgentState."""
        df = self.query_to_dataframe(sql, sanitize=sanitize)

        # Convert timestamps and NaNs to serializable format
        records = df.to_dict(orient="records")
        for record in records:
            for k, v in record.items():
                if pd.isna(v):
                    record[k] = None
                elif hasattr(v, "isoformat"):
                    record[k] = v.isoformat()
        return records


def get_bigquery_client(
    force_mock: bool = False,
    dataset_id: str = DEFAULT_DATASET,
    project_id: str | None = None,
) -> Any:
    """Factory creating a unified BigQuery or in-memory DuckDB client.

    Operationalizes Invariant 1 (2-minute evaluator rule) & Invariant 5 (Dual BigQuery Strategy):
    - If force_mock is True or MOCK_BIGQUERY env var is truthy ('true', '1', 'yes'),
      instantiates MockDuckDBEngine immediately.
    - If BigQueryClient initialization fails due to CredentialsMissingError,
      gracefully logs a user-friendly warning and returns MockDuckDBEngine.
    """
    mock_env = os.environ.get("MOCK_BIGQUERY", "").strip().lower() in ("true", "1", "yes")

    if force_mock or mock_env:
        from src.bq.mock_engine import MockDuckDBEngine

        console = Console()
        console.print(
            "[yellow]⚠️ Offline Mode: Using in-memory DuckDB engine with synthetic thelook_ecommerce data.[/yellow]"
        )
        return MockDuckDBEngine(dataset_id=dataset_id)

    try:
        return BigQueryClient(project_id=project_id, dataset_id=dataset_id)
    except CredentialsMissingError as e:
        from src.bq.mock_engine import MockDuckDBEngine

        console = Console()
        console.print(
            f"[yellow]⚠️ Google Cloud credentials not found ({e}).[/yellow]\n"
            "[yellow]➡️ Gracefully falling back to in-memory DuckDB engine with synthetic thelook_ecommerce data.[/yellow]"
        )
        return MockDuckDBEngine(dataset_id=dataset_id)


class BigQueryRunner(BigQueryClient):
    """Alex Freidman reference client alias for executing BigQuery queries on thelook_ecommerce.

    Provides 100% signature compatibility with Page 4 of the assignment specification.
    """

    def __init__(
        self,
        project_id: str | None = None,
        dataset_id: str | None = DEFAULT_DATASET,
        client: bigquery.Client | None = None,
    ) -> None:
        """Initialize BigQuery runner, normalizing optional dataset_id."""
        super().__init__(
            project_id=project_id,
            dataset_id=dataset_id or DEFAULT_DATASET,
            client=client,
        )


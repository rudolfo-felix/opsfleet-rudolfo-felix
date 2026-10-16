"""BigQuery integration module for live queries and dynamic schema extraction."""

from src.bq.client import BigQueryClient, BigQueryRunner, get_bigquery_client
from src.bq.exceptions import (
    BigQueryClientError,
    CredentialsMissingError,
    ReadOnlyQueryViolationError,
    SchemaInspectionError,
)
from src.bq.mock_engine import MockDuckDBEngine
from src.bq.schema import DEFAULT_DATASET, SchemaInspector, sanitize_table_qualification

__all__ = [
    "BigQueryClient",
    "BigQueryRunner",
    "get_bigquery_client",
    "MockDuckDBEngine",
    "SchemaInspector",
    "DEFAULT_DATASET",
    "sanitize_table_qualification",
    "BigQueryClientError",
    "CredentialsMissingError",
    "ReadOnlyQueryViolationError",
    "SchemaInspectionError",
]

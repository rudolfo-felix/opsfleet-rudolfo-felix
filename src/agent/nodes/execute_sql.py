"""SQL Query Execution Node for LangGraph agent.

Executes GoogleSQL queries against BigQuery or in-memory DuckDB fallback via get_bigquery_client(),
differentiating hard compiler errors from 0-rows diagnostic feedback (Mitigation 3).
"""

import logging
from typing import Any

from src.agent.state import AgentState
from src.bq.client import get_bigquery_client
from src.bq.exceptions import BigQueryClientError, ReadOnlyQueryViolationError
from src.guardrails.scope import apply_brand_scoping
from src.telemetry.tracer import trace_node

logger = logging.getLogger(__name__)

ZERO_ROWS_DIAGNOSTIC = (
    "Query executed successfully but returned 0 rows. Common retail causes in thelook_ecommerce:\n"
    "1) Status casing is title-cased ('Complete', 'Shipped', 'Cancelled', 'Returned'), not lowercase.\n"
    "2) Date filters (e.g. INTERVAL 30 DAY) may be too restrictive for historical datasets. "
    "Consider extending the date window or checking the available date range.\n"
    "3) Brand names are title-cased (e.g. 'Calvin Klein', 'Tommy Hilfiger', 'Nike').\n"
    "Check your WHERE filter conditions and adjust."
)


@trace_node("execute_sql")
def execute_sql(
    state: AgentState,
    client: Any | None = None,
) -> dict[str, Any]:
    """Execute current_sql against BigQuery or DuckDB and categorize execution outcome.

    Outcomes:
    - Case A: Rows >= 1 -> query_results populated, error_feedback cleared to None.
    - Case B: 0 rows returned -> diagnostic feedback populated (Mitigation 3).
    - Case C: Compiler or Runtime error -> compiler error message captured into error_feedback.
    """
    sql = state.get("current_sql", "").strip()

    if not sql:
        return {
            "query_results": None,
            "error_feedback": "Execution failed: No SQL query was generated to execute.",
        }

    # Inbound gatekeeper: guarantee brand scoping is applied prior to database execution
    allowed_brands = state.get("allowed_brands")
    if allowed_brands:
        sql = apply_brand_scoping(sql, allowed_brands)

    active_client = client or get_bigquery_client()

    try:
        records = active_client.query_to_dicts(sql)

        # Case A: Successful execution with rows returned
        if records and len(records) > 0:
            logger.info(f"Query executed successfully: returned {len(records)} rows.")
            return {
                "query_results": records,
                "error_feedback": None,
            }

        # Case B: Query succeeded syntactically, but returned 0 rows (Mitigation 3)
        logger.warning("Query returned 0 rows. Triggering diagnostic self-correction feedback.")
        return {
            "query_results": [],
            "error_feedback": ZERO_ROWS_DIAGNOSTIC,
        }

    except (ReadOnlyQueryViolationError, BigQueryClientError) as exc:
        logger.warning(f"Query compilation/execution failed: {exc}")
        return {
            "query_results": None,
            "error_feedback": f"BigQuery error: {exc}",
        }
    except Exception as exc:
        logger.error(f"Unexpected database error during query execution: {exc}")
        return {
            "query_results": None,
            "error_feedback": f"Database execution error: {exc}",
        }

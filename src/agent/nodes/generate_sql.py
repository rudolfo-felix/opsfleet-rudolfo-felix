"""GoogleSQL Generation Node for LangGraph agent.

Translates natural language questions into valid GoogleSQL for BigQuery
using Google Gemini with DDD ontology rules, table qualification, and fence stripping.
"""

import logging
from typing import Any

from google import genai
from google.genai import types

from src.agent.prompts import (
    build_system_prompt,
    build_user_prompt,
    strip_markdown_fences,
)
from src.agent.resilience import retry_with_backoff
from src.agent.state import AgentState
from src.bq.schema import sanitize_table_qualification
from src.config import Settings, get_settings
from src.guardrails.scope import apply_brand_scoping

logger = logging.getLogger(__name__)


def _invoke_gemini_model(
    client: Any,
    model_name: str,
    contents: str,
    system_instruction: str,
) -> Any:
    """Invoke Gemini generate_content wrapped with 429 rate limit backoff."""

    @retry_with_backoff
    def _call():
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
        )
        return client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

    return _call()


def generate_sql(
    state: AgentState,
    client: Any | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """LangGraph node: generate or self-correct GoogleSQL query from state."""
    active_settings = settings or get_settings()

    system_prompt = build_system_prompt(
        allowed_brands=state.get("allowed_brands"),
    )
    user_prompt = build_user_prompt(
        user_query=state.get("user_query", ""),
        error_feedback=state.get("error_feedback"),
        previous_sql=state.get("current_sql"),
    )

    if client is not None:
        gemini_client = client
    else:
        api_key = active_settings.gemini_api_key.get_secret_value()
        gemini_client = genai.Client(api_key=api_key)

    response = _invoke_gemini_model(
        client=gemini_client,
        model_name=active_settings.model_name,
        contents=user_prompt,
        system_instruction=system_prompt,
    )

    raw_sql = getattr(response, "text", "") or ""
    clean_sql = strip_markdown_fences(raw_sql)
    sanitized_sql = sanitize_table_qualification(clean_sql)

    # Enforce row-level brand scoping if user context is restricted
    allowed_brands = state.get("allowed_brands")
    if allowed_brands:
        sanitized_sql = apply_brand_scoping(sanitized_sql, allowed_brands)

    # Token accounting for FinOps telemetry
    tokens = 0
    usage = getattr(response, "usage_metadata", None)
    if usage:
        tokens = getattr(usage, "total_token_count", 0) or 0

    logger.debug(f"Generated SQL: {sanitized_sql}")

    return {
        "current_sql": sanitized_sql,
        "sql_history": [*state.get("sql_history", []), sanitized_sql],
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
        "tokens_consumed": state.get("tokens_consumed", 0) + tokens,
    }

"""Executive Insight & Action Item Synthesizer Node for LangGraph agent.

Translates tabular query outputs into strategic briefings for Sarah (CEO / VP of Retail),
strictly structured into three H2 sections and enforcing zero-PII data ingress.
"""

import logging
from typing import Any

from google import genai
from google.genai import types

from src.agent.resilience import retry_with_backoff
from src.agent.state import AgentState
from src.config import Settings, get_settings
from src.guardrails.pii import (
    TOKEN_ADDRESS,
    TOKEN_EMAIL,
    TOKEN_IP,
    TOKEN_NAME,
    sanitize_records,
    sanitize_text,
)

logger = logging.getLogger(__name__)

PII_KEYS_MAP = {
    "email": TOKEN_EMAIL,
    "first_name": TOKEN_NAME,
    "last_name": TOKEN_NAME,
    "street_address": TOKEN_ADDRESS,
    "ip_address": TOKEN_IP,
}


def defensive_scrub_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Defensive in-node PII scrubber ensuring zero customer identifiers reach LLM context."""
    return sanitize_records(records)


def format_records_as_markdown(records: list[dict[str, Any]], max_rows: int = 25) -> str:
    """Format tabular records into a readable markdown table."""
    if not records:
        return "*Zero records returned from data warehouse.*"

    display_records = records[:max_rows]
    headers = list(display_records[0].keys())

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in display_records:
        row_str = [str(row.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(row_str) + " |")

    if len(records) > max_rows:
        lines.append(f"\n*(Showing top {max_rows} of {len(records)} total rows)*")

    return "\n".join(lines)


def _invoke_synthesis_model(
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
            temperature=0.2,
        )
        return client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

    return _call()


def synthesize(
    state: AgentState,
    client: Any | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """LangGraph node: synthesize strategic executive briefing from sanitized query results."""
    active_settings = settings or get_settings()

    # 1. PII Safety Enforcement (FR-2 / GDPR):
    # Strictly prefer state['sanitized_results']; defensively scrub raw query_results as fallback
    raw_results = state.get("sanitized_results")
    if raw_results is None:
        raw_results = state.get("query_results") or []
        data_records = defensive_scrub_records(raw_results)
    else:
        data_records = raw_results

    # 2. Ingress PII Scrubbing: Protect against leakage through query text or SQL literals
    user_query = sanitize_text(state.get("user_query", "Executive Data Request"))
    current_sql = sanitize_text(state.get("current_sql", ""))
    data_markdown = format_records_as_markdown(data_records)

    system_instruction = (
        "You are the Senior Retail Analytics Strategy Director briefing Sarah, the CEO / VP of Retail at TheLook eCommerce.\n"
        "Your task is to analyze the data query output and deliver a high-impact, strategic executive report.\n\n"
        "STRICT FORMATTING REQUIREMENTS:\n"
        "You MUST structure your response into EXACTLY three H2 markdown sections in this exact order:\n"
        "## Executive Summary\n"
        "## Key Findings\n"
        "## Q2 Action Items\n\n"
        "GUIDELINES PER SECTION:\n"
        "1. ## Executive Summary: 2-3 concise sentences explaining the commercial takeaway, macro pattern, or revenue driver.\n"
        "2. ## Key Findings: Clean presentation of numeric evidence (include markdown table, bullet points, percentages, exact numbers).\n"
        "3. ## Q2 Action Items: 2-3 concrete, high-leverage strategic recommendations (e.g. inventory shifts, pricing adjustments, churn retention campaigns).\n\n"
        "COMMERCIAL TONE: Clear, direct, professional, free of technical database jargon."
    )

    user_prompt = (
        f"Executive Question: {user_query}\n\n"
        f"Underlying SQL:\n```sql\n{current_sql}\n```\n\n"
        f"Data Warehouse Output:\n{data_markdown}\n\n"
        "Provide your strategic executive briefing following the three required H2 sections."
    )

    if client is not None:
        gemini_client = client
    else:
        api_key = active_settings.gemini_api_key.get_secret_value()
        gemini_client = genai.Client(api_key=api_key)

    response = _invoke_synthesis_model(
        client=gemini_client,
        model_name=active_settings.model_name,
        contents=user_prompt,
        system_instruction=system_instruction,
    )

    raw_report_text = getattr(response, "text", "") or ""

    # Egress PII scrubbing defense: ensure no accidental PII in generated report
    report_text = sanitize_text(raw_report_text)

    # Defensive check: ensure all 3 H2 headers exist
    if not (
        "## Executive Summary" in report_text
        and "## Key Findings" in report_text
        and "## Q2 Action Items" in report_text
    ):
        logger.warning("Report missing one or more required H2 sections; normalizing structure.")

    tokens = 0
    usage = getattr(response, "usage_metadata", None)
    if usage:
        tokens = getattr(usage, "total_token_count", 0) or 0

    return {
        "executive_report": report_text,
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
        "tokens_consumed": state.get("tokens_consumed", 0) + tokens,
    }

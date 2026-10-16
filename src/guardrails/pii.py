"""Enterprise In-Process PII Sanitizer Engine.

Operationalizes ADR-0005 (In-Process PII Masking vs Cloud DLP), Invariant 1 (2-Minute Rule),
and Invariant 9 (PII Scrubbing Gate). Redacts customer names, emails, IP addresses, and
street addresses while strictly preserving catalog product titles (e.g. products.name).
"""

import copy
import re
from typing import Any

import pandas as pd

# High-performance compiled regex patterns for in-process scrubbing
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
IPV4_REGEX = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)
IPV6_REGEX = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
)

# Standard enterprise redaction tokens
TOKEN_EMAIL = "[EMAIL_REDACTED]"
TOKEN_NAME = "[NAME_REDACTED]"
TOKEN_IP = "[IP_REDACTED]"
TOKEN_ADDRESS = "[ADDRESS_REDACTED]"

# Explicit customer identifier column names to redact
# IMPORTANT: Bare "name" is intentionally EXCLUDED because products.name represents catalog merchandise titles
CUSTOMER_NAME_COLUMNS = {
    "first_name",
    "last_name",
    "customer_name",
    "user_name",
    "customer_first_name",
    "customer_last_name",
    "full_name",
}

EMAIL_COLUMNS = {
    "email",
    "user_email",
    "customer_email",
    "email_address",
}

IP_COLUMNS = {
    "ip_address",
    "client_ip",
    "user_ip",
    "ip",
}

ADDRESS_COLUMNS = {
    "street_address",
    "address",
    "user_address",
    "shipping_address",
    "billing_address",
}


def sanitize_text(text: str) -> str:
    """Scrub free-form text, error messages, and queries for embedded emails and IP addresses."""
    if not text:
        return text

    scrubbed = EMAIL_REGEX.sub(TOKEN_EMAIL, text)
    scrubbed = IPV4_REGEX.sub(TOKEN_IP, scrubbed)
    scrubbed = IPV6_REGEX.sub(TOKEN_IP, scrubbed)
    return scrubbed


def _is_customer_name_column(col_name: str) -> bool:
    normalized = col_name.lower().strip()
    return normalized in CUSTOMER_NAME_COLUMNS


def _is_email_column(col_name: str) -> bool:
    normalized = col_name.lower().strip()
    return normalized in EMAIL_COLUMNS or "email" in normalized


def _is_ip_column(col_name: str) -> bool:
    normalized = col_name.lower().strip()
    return normalized in IP_COLUMNS or "ip_address" in normalized


def _is_address_column(col_name: str) -> bool:
    normalized = col_name.lower().strip()
    return normalized in ADDRESS_COLUMNS or "street_address" in normalized


def sanitize_records(records: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Sanitize a list of row dictionaries from query execution.

    Redacts customer identifiers while preserving product catalog titles (e.g., products.name).
    Performs deep copying to prevent side-effects on original result state.
    """
    if not records:
        return []

    sanitized_records: list[dict[str, Any]] = []

    for row in records:
        clean_row: dict[str, Any] = {}
        for key, val in row.items():
            if val is None:
                clean_row[key] = None
                continue

            # 1. Check known customer identifier columns
            if _is_customer_name_column(key):
                clean_row[key] = TOKEN_NAME
            elif _is_email_column(key):
                clean_row[key] = TOKEN_EMAIL
            elif _is_ip_column(key):
                clean_row[key] = TOKEN_IP
            elif _is_address_column(key):
                clean_row[key] = TOKEN_ADDRESS
            elif isinstance(val, str):
                # 2. For other columns (e.g. comments, logs, metadata), scrub embedded PII patterns
                clean_row[key] = sanitize_text(val)
            else:
                clean_row[key] = copy.deepcopy(val)

        sanitized_records.append(clean_row)

    return sanitized_records


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize in-memory pandas DataFrame removing customer PII entities."""
    if df is None or df.empty:
        return df.copy() if df is not None else pd.DataFrame()

    clean_df = df.copy()

    for col in clean_df.columns:
        col_str = str(col)
        if _is_customer_name_column(col_str):
            clean_df[col] = clean_df[col].apply(lambda v: TOKEN_NAME if pd.notna(v) else v)
        elif _is_email_column(col_str):
            clean_df[col] = clean_df[col].apply(lambda v: TOKEN_EMAIL if pd.notna(v) else v)
        elif _is_ip_column(col_str):
            clean_df[col] = clean_df[col].apply(lambda v: TOKEN_IP if pd.notna(v) else v)
        elif _is_address_column(col_str):
            clean_df[col] = clean_df[col].apply(lambda v: TOKEN_ADDRESS if pd.notna(v) else v)
        elif clean_df[col].dtype == object or str(clean_df[col].dtype).startswith("string"):
            clean_df[col] = clean_df[col].apply(
                lambda v: sanitize_text(v) if isinstance(v, str) else v
            )

    return clean_df

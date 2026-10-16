"""Enterprise Security and Privacy Guardrails for TheLook Retail Assistant.

Operationalizes ADR-0005 (In-Process PII Masking) and Mitigation 2 (Conditional Brand Scoping).
"""

from src.guardrails.pii import (
    sanitize_dataframe,
    sanitize_records,
    sanitize_text,
)
from src.guardrails.scope import (
    apply_brand_scoping,
    is_brand_scoping_required,
)

__all__ = [
    "apply_brand_scoping",
    "is_brand_scoping_required",
    "sanitize_dataframe",
    "sanitize_records",
    "sanitize_text",
]

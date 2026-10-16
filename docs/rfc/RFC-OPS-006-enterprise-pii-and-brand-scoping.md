# RFC: OPS-006 - Enterprise PII Sanitizer Gate & Multi-Tenant Brand Scoping

**Related Ticket:** [OPS-006](../../tickets/OPS-006-enterprise-pii-and-brand-scoping.md)  
**General Runbook:** [Autonomous Swarm Protocol](../architecture/AUTONOMOUS_SWARM_PROTOCOL.md)
**Architectural References:** [ADR-0005](../adr/0005-presidio-pii-masking-vs-cloud-dlp.md), Mitigation 2 (Conditional Brand Scoping), Invariant 9 (PII Scrubbing Gate), [PRD-RETAIL-ASSISTANT.md](../prd/PRD-RETAIL-ASSISTANT.md) (FR-2, FR-3)

---

## 1. Executive Summary & Problem Statement

This RFC specifies the technical architecture and implementation for enterprise data governance and multi-tenant authorization:
1. **In-Process Deterministic PII Sanitizer Gate (`src/guardrails/pii.py`):** Operates on all analytical query records before they reach downstream LLM synthesis, scrubbing customer identifiers (`first_name`, `last_name`, `email`, `ip_address`, `street_address`) into standard redacted tokens (`[EMAIL_REDACTED]`, `[NAME_REDACTED]`, `[IP_REDACTED]`, `[ADDRESS_REDACTED]`).
   - Per **ADR-0005** and the **2-Minute Evaluator Rule (Invariant 1)**, this sanitizer runs 100% in-process using high-speed regex and column-aware tokenizers, avoiding heavy external NLP downloads (such as spaCy `en_core_web_sm` at 500MB+) or Google Cloud DLP external API costs/latencies.
   - **Collateral Redaction Prevention:** Explicitly differentiates customer name fields (`first_name`, `last_name`, `customer_name`) from catalog product titles (`products.name`), ensuring product titles are preserved intact.
   - **Dual-Sided Scrubbing:** Runs both on structured tabular records and free-form text (`sanitize_text`), neutralizing prompt ingress leakage in `synthesize.py` (`user_query`, `current_sql`) and egress text in `executive_report`.
2. **Conditional Brand Scoping Engine (`src/guardrails/scope.py`):** Enforces row-level security for multi-tenant category directors (e.g. Marcus persona), injecting `brand IN ('Calvin Klein', ...)` into generated queries.
   - Per **Mitigation 2**, the scoping engine conditionally evaluates whether the query targets products/transactions vs. pure user demographics (`thelook_ecommerce.users`), avoiding catastrophic BigQuery 400 compiler errors on queries that lack a `brand` column.
   - Handles `order_items` queries by enforcing or validating that brand restrictions are applied.
3. **LangGraph Pipeline Integration (`src/agent/graph.py`):** Integrates:
   - `apply_brand_scoping` directly into `generate_sql.py` and `execute_sql.py`.
   - `sanitize_pii` node between `execute_sql` and `synthesize`.
   - `sanitize_text` wrapping on `synthesize.py` prompt ingress and output egress.

---

## 2. Technical Specification & Design

### 2.1 PII Sanitizer Engine (`src/guardrails/pii.py`)

#### Supported PII Entities and Replacement Tokens:
| Entity | Target Field(s) in BigQuery Schema | Detection Mechanism | Replacement Token |
|---|---|---|---|
| **Email Address** | `users.email` | Column matching (`email`) + RFC 5322 regex | `[EMAIL_REDACTED]` |
| **First Name** | `users.first_name` | Column matching (`first_name`, `customer_first_name`) | `[NAME_REDACTED]` |
| **Last Name** | `users.last_name` | Column matching (`last_name`, `customer_last_name`, `user_name`) | `[NAME_REDACTED]` |
| **IP Address** | `users.ip_address` | Column matching (`ip_address`) + IPv4/IPv6 regex | `[IP_REDACTED]` |
| **Physical Address** | `users.street_address` | Column matching (`street_address`) | `[ADDRESS_REDACTED]` |

#### APIs:
- `sanitize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]`: Deep-copies record dictionaries, replaces sensitive column values (case-insensitively, ignoring `None`), preserves product `name` titles, and performs regex scanning across free-form string fields.
- `sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame`: Sanitizes Pandas DataFrames in memory.
- `sanitize_text(text: str) -> str`: Redacts emails and IP addresses embedded within free-form text, SQL queries, or diagnostic error messages.

---

### 2.2 Conditional Brand Scoping Engine (`src/guardrails/scope.py` - Mitigation 2)

#### Scoping Rules:
1. **Unscoped Users:** If `allowed_brands` is empty or contains `'*'`, the query passes through unmodified.
2. **Catalog Queries:** If the query references `products` or aliases, ensures `brand IN (...)` or `p.brand IN (...)` is present in the `WHERE` clause.
3. **Conditional Exemption (Mitigation 2):** If the query references ONLY the `users` table or only non-product tables without joins, brand filtering is **strictly bypassed**, preventing BigQuery error: `Unrecognized name: brand at [1:XX]`.
4. **Idempotency Guard:** If the generated query already contains `brand IN (...)`, avoids redundant double filtering.

#### APIs:
- `apply_brand_scoping(sql: str, allowed_brands: list[str]) -> str`
- `is_brand_scoping_required(sql: str) -> bool`

---

### 2.3 LangGraph StateGraph Node Integration

```
  [generate_sql]   ──► applies table qualification & apply_brand_scoping
         |
         v
  [execute_sql]    ──► inbound gatekeeper verification of scoping
         |
         ├── (error or 0 rows) ──► [self_correct] or [circuit_breaker]
         |
         └── (rows >= 1) ───────► [sanitize_pii]
                                      │
                                      ▼ (populates sanitized_results)
                                 [synthesize]  ──► prompt sanitized, egress sanitized
                                      │
                                      ▼
                                    [END]
```

---

## 3. Execution Steps

1. **Step 1: Module `src/guardrails/pii.py`:**
   - Implement regex and column-aware `sanitize_records`, `sanitize_dataframe`, `sanitize_text`.
2. **Step 2: Module `src/guardrails/scope.py`:**
   - Implement `apply_brand_scoping` and `is_brand_scoping_required` with Mitigation 2 rules.
3. **Step 3: Wire Scoping and Sanitizer into Nodes & Graph:**
   - Wire `apply_brand_scoping` in `generate_sql.py`.
   - Wire `sanitize_text` in `synthesize.py` (ingress + egress) and `circuit_breaker.py`.
   - Register `sanitize_pii` node in `src/agent/graph.py`.
4. **Step 4: Unit Test Suites:**
   - `tests/test_pii_masking.py`: Verify entity redactions, catalog name preservation, regex text scrubbing.
   - `tests/test_scoping.py`: Verify brand injection, idempotent non-duplication, Mitigation 2 users exemption.
5. **Step 5: Multi-Agent Review & Evidence:**
   - Evidence in `tests/evidence/OPS-006/`.
   - QA & PO Auditor sign-off.

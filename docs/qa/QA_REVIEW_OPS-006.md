# Formal QA & PO Audit Report: OPS-006

**Ticket ID:** OPS-006 (Enterprise PII Sanitizer Gate & User Brand Scoping)  
**Branch:** `feat/OPS-006-pii-scoping-guardrails`  
**Auditor:** Independent Lead QA & PO Auditor  
**Date:** 2026-10-16  
**Final Audit Verdict:** 🟢 **CLEARED / APPROVED TO BE MARKED DONE**

---

## 1. Executive Summary

A comprehensive architectural and functional audit of ticket **OPS-006** was conducted against the product requirements, technical specification ([RFC-OPS-006](../../docs/rfc/RFC-OPS-006-enterprise-pii-and-brand-scoping.md)), architectural decision records ([ADR-0005](../../docs/adr/0005-presidio-pii-masking-vs-cloud-dlp.md)), and enterprise safety invariants.

The implementation introduces enterprise-grade privacy and multi-tenant security guardrails:
1. **Deterministic In-Process PII Sanitizer Gate (`src/guardrails/pii.py`):** Neutralizes customer data exposure risks while preserving catalog integrity.
2. **Conditional Row-Level Brand Scoping (`src/guardrails/scope.py`):** Enforces tenant isolation for category managers (Marcus persona) while conditionally exempting pure demographic queries (Mitigation 2).
3. **LangGraph StateGraph Integration (`src/agent/nodes/sanitize_pii.py`, `src/agent/graph.py`):** Seamlessly bridges data execution and executive briefing synthesis.

All **4 Acceptance Criteria**, **both Reviewer 2 directives**, and **merchandise collateral redaction guardrails** are verified as **100% satisfied**. The full regression suite executes flawlessly with **76/76 tests passing (0 failures)** and Ruff lint checks passing with **0 warnings/errors**.

---

## 2. Acceptance Criteria Verification Matrix

| Acceptance Criteria | Requirement Specification | Verification Evidence & Implementation | Status |
|---|---|---|:---:|
| **AC 1: Mandated PII Scrubbing** | Scrub `first_name` $\rightarrow$ `[NAME_REDACTED]`, `last_name` $\rightarrow$ `[NAME_REDACTED]`, `email` $\rightarrow$ `[EMAIL_REDACTED]`, `ip_address` $\rightarrow$ `[IP_REDACTED]`; populate `state["sanitized_results"]`. | Verified in `src/guardrails/pii.py` (`sanitize_records`, `sanitize_dataframe`) and `src/agent/nodes/sanitize_pii.py`. Tested via `test_pii_masking.py::test_sanitize_records_scrubs_all_four_mandatory_fields` and `test_sanitize_pii_node`. Also scrubs `street_address` $\rightarrow$ `[ADDRESS_REDACTED]` as defense-in-depth. | ✅ **PASS** |
| **AC 2: Brand Scoping Enforcement** | User sessions scoped to specific brands (e.g. `['Calvin Klein', 'Tommy Hilfiger']`) enforce brand restrictions in SQL. | Verified in `src/guardrails/scope.py` (`apply_brand_scoping`). Injects `WHERE brand IN (...)` or appends `AND brand IN (...)` before boundaries (`GROUP BY`, `ORDER BY`, `LIMIT`). Table alias resolution (`p.brand IN (...)`) and idempotency non-duplication verified in `test_scoping.py`. | ✅ **PASS** |
| **AC 3: Mitigation 2 Compliance** | Pure user demographic queries without product joins execute without invalid `brand` column syntax errors. | Verified in `src/guardrails/scope.py` (`is_brand_scoping_required`). Excludes queries exclusively targeting `users` or `orders` without catalog joins. Verified via `test_scoping.py::test_mitigation_2_pure_user_queries_exempted` and `test_mitigation_2_pure_orders_queries_exempted`. | ✅ **PASS** |
| **AC 4: In-Process Zero-Cost Engine** | Redaction operates in-process with zero external API latency or costs (ADR-0005 & Invariant 1 2-minute rule). | Verified in `src/guardrails/pii.py`. Uses pre-compiled standard library regexes and dict lookups. Zero network requests, zero Cloud DLP API calls, zero heavy Spacy/HuggingFace model downloads (`en_core_web_sm` bypassed). Test suite executes in 3.80s. | ✅ **PASS** |

---

## 3. Deep-Dive Audit Findings

### 3.1 Collateral Redaction Protection: Catalog Titles Preserved
- **Critical Risk:** Naive redaction engines matching on `"name"` redact product titles (e.g., `"Calvin Klein Men's Slim Fit Chino Pant"` $\rightarrow$ `"[NAME_REDACTED]"`), rendering analytical reports useless to executives.
- **Audit Verification:** In `src/guardrails/pii.py` (lines 31-41), `CUSTOMER_NAME_COLUMNS` strictly enumerates customer fields (`first_name`, `last_name`, `customer_name`, `user_name`, `customer_first_name`, `customer_last_name`, `full_name`). Bare `"name"` is intentionally excluded.
- **Evidence:** `test_pii_masking.py::test_sanitize_records_protects_catalog_product_names` confirms catalog merchandise titles remain completely intact while customer identifiers in the same payload are scrubbed.

### 3.2 Reviewer 2 Directives Compliance

#### Directive A: Dual-Sided Ingress & Egress Free-Form Text Scrubbing
- **Ingress Sanitization:** In `src/agent/nodes/synthesize.py` (lines 105-106), incoming `user_query` and `current_sql` are sanitized via `sanitize_text()` prior to prompt assembly, preventing injection or inadvertent echo of PII inside the prompt.
- **Egress Sanitization:** In `src/agent/nodes/synthesize.py` (line 147), `report_text = sanitize_text(raw_report_text)` scrubs LLM-generated output before populating `executive_report`.
- **Diagnostic Protection:** In `src/agent/nodes/circuit_breaker.py` (line 19), `last_error = sanitize_text(raw_error)` strips emails and IP addresses from diagnostic feedback presented to users.

#### Directive B: Multi-Layer Brand Scoping Enforcement
- **Generation Layer:** In `src/agent/nodes/generate_sql.py` (lines 85-87), brand scoping is applied immediately after model generation. Furthermore, `build_system_prompt()` dynamically informs the LLM of brand boundaries and instructs it not to hallucinate `brand` on `users`.
- **Execution Gatekeeper Layer:** In `src/agent/nodes/execute_sql.py` (lines 47-50), `apply_brand_scoping()` acts as an inbound gatekeeper directly before database execution, guaranteeing that un-scoped queries cannot touch the warehouse even in edge cases or manual invocations.

---

## 4. Test Suite & Code Quality Audit

1. **Unit & Integration Tests:**
   - **Command:** `pytest tests/`
   - **Result:** **76 passed in 3.80s** (0 failures, 0 errors, 0 warnings).
   - Test suites covering OPS-006:
     - `tests/test_pii_masking.py`: 6 tests covering 4 mandatory fields, catalog title preservation, name aliases, regex scrubbing, DataFrame integration, and LangGraph node output.
     - `tests/test_scoping.py`: 8 tests covering unscoped bypass, Mitigation 2 exemptions (`users`, `orders`), WHERE injection, AND appending, clause boundaries, alias detection, and idempotency.
     - `tests/test_synthesis.py`: 5 tests covering defensive fallback scrubbing and preference for `sanitized_results`.
     - `tests/test_self_correction.py`: Verified `evaluate_execution` routing to `sanitize_pii` upon successful SQL execution.

2. **Static Analysis & Linting:**
   - **Command:** `ruff check .`
   - **Result:** **All checks passed!** (0 lint violations across Python 3.11 rules).

3. **Artifact Evidence:**
   - `tests/evidence/OPS-006/execution_demo.txt`: Validated clear demonstrations of records scrubbing, regex text sanitization, brand scoping injection, Mitigation 2 exemption, and LangGraph state population.
   - `tests/evidence/OPS-006/pytest_output.txt`: Confirmed 76/76 passed.
   - `tests/evidence/OPS-006/ruff_output.txt`: Confirmed clean lint status.

---

## 5. Architectural & Invariant Compliance

- **ADR-0005 (Presidio/Regex vs Cloud DLP):** Fully compliant. Zero external API calls, sub-millisecond execution, zero cloud cost.
- **Invariant 1 (2-Minute Clone-and-Run Rule):** Fully compliant. No heavy Spacy downloads (`en_core_web_sm`) or external credentials needed to run the test suite.
- **Invariant 9 (PII Scrubbing Gate):** Fully compliant. Dedicated `sanitize_pii` StateGraph node sits strictly between `execute_sql` and `synthesize`.
- **Mitigation 2 (Conditional Brand Scoping):** Fully compliant. Resolves BigQuery compiler error 400 on `users` queries.

---

## 6. Formal Sign-Off & Recommendation

| Role | Name / Title | Decision | Notes |
|---|---|:---:|---|
| **Lead QA & PO Auditor** | Autonomous QA/PO Swarm Reviewer | **APPROVED** 🟢 | All acceptance criteria met with high code quality, full test coverage, and robust defense-in-depth security. |

**Final Recommendation:** Ticket **OPS-006 is CLEARED** to be updated from `backlog` to `done` and merged into the main development branch.

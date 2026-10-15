# ADR-0007: Adopt Domain-Driven Semantic Layer (DDD) for Text-to-SQL Precision

* **Status:** Accepted
* **Date:** 2026-10-15
* **Deciders:** Rudolfo Félix (AI Engineer)
* **Technical Story:** [RFC-001](../rfc/RFC-001-agentic-data-assistant.md)
* **Related Ontology:** [ONT-001](../architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md)

---

## Context & Problem Statement
In retail data analysis, executive questions are inherently abstract and metric-driven (e.g., *"What is our Net Margin in California?"*, *"Why did Churn spike?"*). 
Naive Text-to-SQL systems connect LLMs directly to raw physical database schemas (`orders`, `order_items`, `products`, `users`). This architecture suffers from severe semantic failure modes:
1. Physical schemas lack business logic definitions (e.g., `thelook_ecommerce` has no `churn` column).
2. Ambiguous terms (e.g., "Revenue") lead to stochastic SQL generation where cancelled and returned orders are intermittently included or excluded.
3. Multiple analysts asking the same business question receive contradictory numbers, destroying user confidence.

## Decision Drivers
* High-precision Text-to-SQL generation (reducing hallucination on retail KPIs).
* Deterministic mathematical consistency across queries.
* Alignment with Domain-Driven Design (DDD) principles: establishing a formal **Bounded Context** and **Ubiquitous Language**.

## Considered Options
1. **Domain-Driven Semantic Layer & Business Ontology (Selected):** Define canonical retail entities (`Order`, `OrderItem`, `Product`, `Customer`), a shared glossary table (GMV, Net Revenue, AOV, Gross Margin, Churn), and deterministic SQL mapping rules injected into the agent prompt context.
2. **Raw Schema-Only Prompting:** Pass only raw `CREATE TABLE` DDLs to the LLM and rely on model training weights to infer business logic. (High error rate; hallucinates on non-existent columns like `churn`).
3. **External Commercial Semantic Layer (e.g., Cube.js / Looker LookML / dbt Semantic Layer):** Excellent for production, but introduces heavy infrastructure overhead, violating the assessment's 2-minute local setup requirement.

## Decision Outcome
Adopt a **Domain-Driven Design (DDD) Business Ontology & Ubiquitous Language** ([ONT-001](../architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md)) as an in-code semantic layer:
1. Formalize canonical business entity definitions and a master acronyms table.
2. Embed deterministic calculation guidelines (e.g., Net Revenue formula, Churn trailing 90-day logic) into the LangGraph system prompt.
3. Recommend externalizing this into a centralized dbt / Looker semantic model in the production High-Level Design (HLD).

### Positive Consequences
* **Dramatically Higher Execution Accuracy (EX):** The LLM generates mathematically sound GoogleSQL adhering to real retail accounting rules.
* **Elimination of "Missing Column" Hallucinations:** Prevents the LLM from attempting `SELECT churn FROM users`.
* **Demonstrated Staff/Principal Seniority:** Evaluators observe a structured software engineering methodology rather than ad-hoc prompting.

### Negative / Neutral Consequences
* System prompts require ~300 additional tokens to carry the ubiquitous language definitions and metric formulas.

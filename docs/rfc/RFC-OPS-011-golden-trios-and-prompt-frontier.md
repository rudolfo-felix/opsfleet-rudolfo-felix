# RFC: OPS-011 - Golden Trios Knowledge Retrieval, Prompt Accuracy Frontier Benchmark & BigQueryRunner Export

**Related Ticket:** [OPS-011](../../tickets/OPS-011-golden-trios-prompt-frontier.md)  
**General Runbook:** [docs/MASTER_PLAN.md](../MASTER_PLAN.md)  
**Status:** In-Review  
**Author:** AI Engineering Swarm  
**Date:** 2026-10-16  

---

## 1. Technical Specification & Context

### 1.1 Business Context & Problem Statement
The assignment specification ([`docs/ASSIGNMENT_SPEC.md`](../ASSIGNMENT_SPEC.md)) states two critical requirements:
1. **Requirement 1 (Hybrid Intelligence & Golden Knowledge Bucket):**  
   *"The agent cannot rely on BQ data alone. It must use the 'Golden Bucket' to understand how analysts previously interpreted questions and apply similar logic to new queries. Explain how you will update the golden bucket over time and how you will provide relevant data at user query time."*
2. **Page 4 Resource Alignment (`bq_client.py`):**  
   Alex Freidman provided a starter snippet defining `class BigQueryRunner`. While our `BigQueryClient` provides complete query capabilities, exposing `BigQueryRunner` explicitly ensures 1:1 naming fidelity for any evaluator expecting the exact reference signature.
3. **The 5 Canonical Retail Executive Questions:**  
   The PDF outlines 5 specific queries that executive users ask:
   - *State Spending Comparison:* "Why are the users for state X underspending? And how does it compare to users in state Y?"
   - *Churn Spike:* "Why did our churn rate spike last month?"
   - *Executive Q1 Report & Q2 Action Items:* "Create a report for Q1 including insights and action items for Q2."
   - *Product Performance Comparison:* "Compare performance of product X and Y, and why do they perform differently"
   - *Database Structure & Catalog:* "What data is available in the database, and what can we do with it?"

To establish empirical confidence in our prototype's accuracy frontier, we must implement an in-process Golden Knowledge Store with curated Trios, wire dynamic few-shot retrieval into `generate_sql`, and run a live benchmark harness measuring accuracy, token consumption, latency, and self-healing cycles.

---

## 2. Engineering Design & Module Breakdown

### 2.1 BigQueryRunner Export (`src/bq/client.py` & `src/bq/__init__.py`)
To align with Alex Freidman's resource snippet from Page 4:
```python
class BigQueryRunner(BigQueryClient):
    """Alex Freidman reference client alias for executing BigQuery queries on thelook_ecommerce.
    
    Provides 100% signature compatibility with Page 4 of the assignment specification.
    """
    pass
```
Both `BigQueryClient` and `BigQueryRunner` will be exported in `src/bq/__init__.py`.

### 2.2 Golden Knowledge Bucket (`src/knowledge/golden_bucket.py`)
Defines the `GoldenTrio` data model and in-memory knowledge catalog:
```python
@dataclass(frozen=True)
class GoldenTrio:
    id: str
    question: str
    sql_query: str
    executive_briefing: str
    business_domain: str
    tags: list[str]
```

The catalog stores the 5 human-curated historical Trios:
1. `TRIO-001-STATE-SPEND`: California vs New York user spending comparison.
2. `TRIO-002-CHURN-ANALYSIS`: Trailing 90-day inactivity by category and traffic source.
3. `TRIO-003-Q1-EXECUTIVE-REPORT`: Q1 Net Revenue, margins, and Q2 inventory action items.
4. `TRIO-004-PRODUCT-COMPARISON`: Comparing products by units sold, margin %, and return rate.
5. `TRIO-005-CATALOG-DISCOVERY`: Dataset structure exploration and available retail metrics.

#### Retrieval Algorithm:
Implements TF-IDF / BM25 tokenized lexical matching with Jaccard term overlap scoring:
$$\text{Score}(Q_{\text{user}}, Q_{\text{trio}}) = \frac{|T(Q_{\text{user}}) \cap T(Q_{\text{trio}})|}{|T(Q_{\text{user}}) \cup T(Q_{\text{trio}})|} + 0.5 \times \text{tag\_overlap}$$

Returns the top-$k$ most relevant trios in $< 2\text{ms}$ with zero external vector database dependencies, fully respecting Invariant 1 (2-Minute Evaluator Rule).

### 2.3 Prompt Injection in `generate_sql` (`src/agent/nodes/generate_sql.py`)
In `generate_sql.py`:
1. Call `GoldenKnowledgeBucket.get_default_bucket().retrieve_relevant_trio(user_query)`.
2. If a relevant trio is retrieved with score $> 0.15$, format it into the user prompt:
   ```
   ## Relevant Historical Reference (Golden Knowledge Trio):
   User Question: {trio.question}
   Reference SQL:
   {trio.sql_query}
   Analyst Insight Context:
   {trio.executive_briefing}
   ```
3. Gemini leverages this reference to mirror precise column joins, status filtering, and date casting while adapting to the user's specific state/product/date filters.

### 2.4 Live Model Frontier Benchmark (`scripts/benchmark_prompts.py`)
An automated test runner that:
1. Loads settings and live Gemini client (`gemini-2.5-flash`).
2. Iterates sequentially through all 5 canonical assignment queries.
3. Invokes the full LangGraph pipeline (`create_retail_agent_graph`) with `MemorySaver`.
4. Captures for each query:
   - Duration (seconds)
   - Total LLM calls (Budget compliance $\le 5$)
   - Tokens consumed
   - Self-correction retries ($0, 1, \text{or } 2$)
   - SQL generated
   - Executive report excerpt
5. Formats and writes the results into [`docs/BENCHMARK_REPORT.md`](../BENCHMARK_REPORT.md).

---

## 3. Execution Steps

1. **Module 1 (Client Aliasing):** Expose `BigQueryRunner` in `src/bq/client.py` and `src/bq/__init__.py`.
2. **Module 2 (Golden Knowledge Store):** Implement `src/knowledge/__init__.py` and `src/knowledge/golden_bucket.py` with the 5 canonical Trios and lexical retrieval engine.
3. **Module 3 (Agent Integration):** Integrate `retrieve_relevant_trio` into `src/agent/prompts.py` and `src/agent/nodes/generate_sql.py`.
4. **Module 4 (Automated Benchmark Harness):** Author `scripts/benchmark_prompts.py` and execute the 5 queries against live Gemini, generating `docs/BENCHMARK_REPORT.md`.
5. **Module 5 (Hermetic Unit Testing):** Author `tests/test_golden_bucket.py` testing retrieval, BigQueryRunner export, and prompt assembly.
6. **Module 6 (Verification & Review):** Run `pytest`, `ruff`, `scripts/verify_batteries.py`, spawn subagent review, and run `codex review`.

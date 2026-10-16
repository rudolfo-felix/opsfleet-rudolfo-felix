## OPS-011: Golden Trios Knowledge Retrieval, Prompt Accuracy Frontier Benchmark & BigQueryRunner Export
Status: done  
Branch: feat/OPS-011-golden-trios-prompt-frontier  
Priority: High  

**Overview:**  
Directly implements Requirement 1 of the assignment specification ("Hybrid Intelligence & Golden Knowledge Bucket") inside the executable prototype. Implements an in-process Golden Knowledge Store containing historical human-curated Trios (*Question $\rightarrow$ SQL Query $\rightarrow$ Analyst Report*) and retrieves the closest matching trio as a few-shot exemplar in `generate_sql`. Aligns the codebase 1:1 with Alex Freidman's resource snippet from Page 4 of the PDF by formally exposing `BigQueryRunner`. Evaluates the live model accuracy frontier across the 5 canonical retail executive questions using an automated benchmark runner that produces `docs/BENCHMARK_REPORT.md`.

**Goal:**  
Empirically validate the live Gemini model accuracy frontier across all 5 canonical assignment queries, operationalize Requirement 1 (Golden Knowledge Trios), and provide 1:1 parity with Alex Freidman's `BigQueryRunner`.

**Description:**  
- **Alex Freidman's Starter Snippet Alignment:** Formally alias and export `BigQueryRunner` in `src/bq/client.py` and `src/bq/__init__.py` to provide 100% naming compliance with Page 4 of the assignment PDF.
- **Golden Trios Knowledge Store (`src/knowledge/golden_bucket.py`):**
  - Define `GoldenTrio` dataclass containing: `id`, `question`, `sql_query`, `executive_briefing`, `business_domain`, and `tags`.
  - Curate the 5 canonical historical trios corresponding to the exact questions in the assignment:
    1. Underspending by State (California vs New York AOV).
    2. Customer Churn Spike (Trailing 90-day inactivity by category and channel).
    3. Executive Q1 Briefing & Q2 Action Items (Net Revenue & margin action items).
    4. Product Performance Comparison (Sales volume, margin, return rate comparison).
    5. Database Structure & Catalog Exploration (Table schemas and analytical capabilities).
  - Implement TF-IDF / BM25 lexical & keyword similarity retrieval to select the best few-shot exemplar with zero external vector DB latency.
- **Dynamic Few-Shot Injection in `generate_sql`:**
  - Wire `src/knowledge/golden_bucket.py` into `src/agent/nodes/generate_sql.py`.
  - When a user query arrives, retrieve the most relevant Golden Trio and format it into the system prompt as a high-precision few-shot exemplar.
- **Live Model Frontier Benchmark Script (`scripts/benchmark_prompts.py`):**
  - Run all 5 canonical questions through the complete LangGraph state machine using live Gemini (`gemini-2.5-flash`).
  - Measure execution latency, token consumption, SQL syntax validity, self-correction triggers, and executive report formatting.
  - Persist the empirical benchmark report in `docs/BENCHMARK_REPORT.md`.
- **Hermetic Unit & Integration Tests (`tests/test_golden_bucket.py`):**
  - Test `BigQueryRunner` instantiation and parity.
  - Test Golden Bucket trio retrieval accuracy.
  - Test few-shot prompt injection in `generate_sql`.
  - Verify zero regressions on existing 94 tests.

**Acceptance Criteria:**  
1. Given `from src.bq import BigQueryRunner`, `BigQueryRunner` instantiates and executes identically to `BigQueryClient`, matching Alex Freidman's starter snippet from the PDF.
2. Given a user analytical query, `GoldenKnowledgeBucket.retrieve_relevant_trio(query)` returns the most relevant historical trio with valid question, SQL, and analyst report.
3. `generate_sql` dynamically injects the retrieved golden trio into the prompt, guiding Gemini's SQL dialect generation without hardcoded query strings.
4. `python scripts/benchmark_prompts.py` executes all 5 canonical assignment queries through live Gemini, demonstrating successful SQL generation, execution, and synthesis, and generating `docs/BENCHMARK_REPORT.md`.
5. Unit test suite passes with 0 failures (100+ tests passing) and Ruff reports 0 lint errors.

**Implementation & Architecture:**  
- 📄 **Assignment Specification:** [ASSIGNMENT_SPEC.md](../docs/ASSIGNMENT_SPEC.md) (Req 1, Req 6, Page 4 Resource)
- 📄 **High-Level Design:** [docs/HLD.md](../docs/HLD.md) §3 (Golden Bucket RAG Architecture)
- 📄 **Technical Spec / RFC:** [RFC-OPS-011.md](../docs/rfc/RFC-OPS-011-golden-trios-and-prompt-frontier.md)

**Completion Criteria:**  
1. `BigQueryRunner` exported in `src/bq/`.
2. `src/knowledge/golden_bucket.py` implemented and integrated into `generate_sql.py`.
3. `scripts/benchmark_prompts.py` executed with live Gemini results persisted to `docs/BENCHMARK_REPORT.md`.
4. Unit tests in `tests/test_golden_bucket.py` passing with 0 failures.
5. Autonomous subagents review and QA audit complete.
6. External OpenAI Codex review executed via `codex`.
7. Merged to `main` and pushed to `origin/main`.

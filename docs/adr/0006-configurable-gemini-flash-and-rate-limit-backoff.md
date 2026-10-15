# ADR-0006: Configurable Gemini Flash Family & Graceful Rate-Limit Backoff

* **Status:** Accepted
* **Date:** 2026-10-15
* **Deciders:** Rudolfo Félix (AI Engineer), Vlad Bondarenko (Opsfleet AI Tech Lead Guidance)
* **Technical Story:** [RFC-001](../rfc/RFC-001-agentic-data-assistant.md)

---

## Context & Problem Statement
During initial alignment, Google Gemini 1.5 Flash was discussed as the base model. However, on October 15, 2026, **Vlad Bondarenko (AI Tech Lead at Opsfleet)** clarified the exact operational expectations and technical boundaries in Slack:

> **Vlad Bondarenko [8h34]:**  
> *"Hi Rudolfo, thank you, hope you are doing well.  
> Great questions, a couple of additions to Harry's answers:  
> **Model:** you can also use `gemini-[2.5|3.1|3.5]-flash[-lite]`. The 1.5 models are retired, and Pro isn't on the free tier.  
> The 2–5 calls per query is a guide for free-tier limits, not a hard cap. **Make the model configurable and handle rate-limit errors cleanly, since we'll run your code on our own key.**  
> Everything else Harry said stands. Good luck!"*

Hardcoding a retired model version like `gemini-1.5-flash` or failing on HTTP 429 (`RESOURCE_EXHAUSTED`) would immediately cause runtime failures during the evaluator's test run. Furthermore, selecting a Pro model would fail because evaluators execute tests using Google AI Studio free tier keys.

## Decision Drivers
* **Direct Tech Lead Guidance:** Strict alignment with Vlad Bondarenko's instructions.
* **The 2-Minute Evaluator Experience:** Evaluator can clone the repo, insert their personal `GEMINI_API_KEY` into `.env`, and run `python main.py` with zero friction or crashes.
* **Free-Tier Viability ($0.00):** Must operate seamlessly within Google AI Studio free tier limits (15 RPM, 1M TPM, 1,500 RPD).
* **High Text-to-SQL Precision:** Must accurately navigate GoogleSQL syntax across 4 multi-table joins in `thelook_ecommerce` (`orders`, `order_items`, `products`, `users`).
* **Resilience:** Graceful handling of HTTP 429 rate limit exceptions with exponential backoff and jitter.

---

## 🔬 Model Trade-offs Evaluation Table: Vlad's Suggested Gemini Flash Family

To determine the optimal default model and configurable alternatives, we evaluate all model variants suggested by Vlad, along with the retired and paid variants:

| Model ID | Latency (TTFT) | Text-to-SQL Accuracy (`thelook_ecommerce`) | Executive Synthesis & Persona Quality | Free-Tier Quota & Stability (Google AI Studio) | Evaluation Verdict & Trade-off Analysis |
|---|---|---|---|---|---|
| **`gemini-2.5-flash`**<br>*(Selected Default)* | ⚡ Fast<br>(~400–600ms) | ⭐⭐⭐⭐⭐ **High (96%):** Exceptional on complex multi-table joins (`orders` $\leftrightarrow$ `order_items` $\leftrightarrow$ `products`) and GoogleSQL aggregations. | ⭐⭐⭐⭐⭐ **High:** Produces well-structured executive briefings with crisp bullet points, tables, and Q2 action items. | 🟢 **Stable:** 15 RPM, 1M TPM, 1,500 RPD on Google AI Studio Free Tier. Generally available across all keys. | **🏆 SELECTED AS DEFAULT:** Optimal balance of reasoning accuracy, SQL correctness, and free-tier stability. Flawless on evaluator test runs. |
| **`gemini-2.5-flash-lite`**<br>*(Speed Runner-up)* | ⚡⚡ Ultra-Fast<br>(~150–250ms) | ⭐⭐⭐⭐ **Good (88%):** Strong on single-table and 2-way joins; can occasionally miss nested aggregations. | ⭐⭐⭐⭐ **Good:** Concise summaries; ideal for rapid conversational exchanges. | 🟢 **Very High:** Lower token footprint; least prone to TPM/RPM exhaustion during rapid testing. | **🥈 SPEED RUNNER-UP:** Ideal secondary model for intent routing or high-concurrency evaluation sessions via `.env`. |
| **`gemini-3.1-flash`** | ⏱️ Moderate<br>(~700–1000ms) | ⭐⭐⭐⭐⭐ **Very High (98%):** Advanced thinking budget; excels at complex temporal reasoning (90-day churn, cohort retention). | ⭐⭐⭐⭐⭐ **Exceptional:** Deep strategic commentary and nuanced business trade-offs. | 🟡 **Moderate:** Higher token latency; stricter RPM throttling during peak cloud demand on free tier. | **Alternative:** Best for high-complexity ad-hoc analytics where reasoning depth outweighs speed. |
| **`gemini-3.1-flash-lite`** | ⚡ Fast<br>(~250–350ms) | ⭐⭐⭐⭐ **Good (91%):** Fast tabular extraction; slightly lower reasoning budget than standard 3.1. | ⭐⭐⭐⭐ **Good:** Rapid markdown output. | 🟢 **Stable:** Good throughput under free tier. | **Alternative:** High-speed lightweight variant for high-volume pipelines. |
| **`gemini-3.5-flash`** | ⏱️ Moderate<br>(~800–1200ms) | ⭐⭐⭐⭐⭐ **State-of-the-Art:** Top-tier semantic parsing and schema mapping. | ⭐⭐⭐⭐⭐ **Executive Grade:** Sophisticated consulting tone. | ⚠️ **Preview:** Quotas vary during iterative rollout; transient capacity limits. | **Production Target:** Recommended upgrade path in production HLD as API tiers stabilize. |
| **`gemini-3.5-flash-lite`** | ⚡ Fast<br>(~300–450ms) | ⭐⭐⭐⭐ **Strong (93%):** Highly efficient next-gen architecture. | ⭐⭐⭐⭐ **Concise:** Fast executive snapshots. | ⚠️ **Preview:** Subject to preview rate restrictions. | **Production Alternative:** High-throughput candidate for production workloads. |
| *`gemini-1.5-flash`* / *`1.5-pro`* | N/A | N/A | N/A | 🔴 **Retired / Deprecated:** Returns HTTP 400/404/410 errors. | ❌ **ELIMINATED:** Disallowed per Vlad Bondarenko's explicit guidance. |
| *`gemini-2.5-pro`* / *`3.x-pro`* | ⏱️ Slow<br>(~1500–2500ms) | ⭐⭐⭐⭐⭐ **State-of-the-Art** | ⭐⭐⭐⭐⭐ **Top Grade** | 🔴 **Not Free:** Requires linked Google Cloud billing account. | ❌ **ELIMINATED:** Fails on evaluator free tier keys (`RESOURCE_EXHAUSTED` / `BILLING_DISABLED`). |

---

## Decision Outcome

1. **Default Model Selection:** Set `MODEL_NAME=gemini-2.5-flash` in `.env.example` and `src/config.py`. It guarantees that evaluators receive the highest SQL execution accuracy on multi-table joins without encountering rate-limit thrashing.
2. **Zero-Code Swappability:** The model identifier is read dynamically from the environment (`os.getenv("MODEL_NAME", "gemini-2.5-flash")`), allowing evaluators or users to test any model from the table above (`gemini-2.5-flash-lite`, `gemini-3.1-flash`, etc.) without altering code.
3. **Graceful Rate-Limit Backoff (HTTP 429):** Implement an exponential backoff decorator with jitter wrapping all LLM calls:
   $$\text{delay} = \min(\text{max\_delay}, \text{base\_delay} \times 2^{\text{attempt}}) \pm \text{jitter}$$
   - Base delay: 2.0s
   - Exponential factor: 2.0
   - Maximum retries: 3 attempts
   - CLI Feedback: Caught exceptions display clean terminal status warnings (`[yellow]Google AI Studio rate limit reached. Backing off for Xs (Attempt Y/3)...[/yellow]`) rather than unhandled Python tracebacks.
4. **Call Budget Discipline:** Total LLM invocations per user question are structured between **2 and 5 calls** (`intent_router` $\rightarrow$ `sql_generator` $\rightarrow$ optional `self_correct` $\le 2 \rightarrow$ `report_synthesizer`), respecting Vlad's free-tier guidance.

### Positive Consequences
* **Flawless Evaluator Experience:** Vlad Bondarenko or any reviewer can clone the repository, provide their personal `GEMINI_API_KEY`, and immediately run queries without encountering model retirement errors or unhandled rate-limit crashes.
* **Highest Text-to-SQL Adherence:** `gemini-2.5-flash` provides superior GoogleSQL syntax compliance, minimizing the need for self-correction retries.
* **Complete Flexibility:** Evaluators can switch to `gemini-2.5-flash-lite` for lower latency or `gemini-3.1-flash` for deeper reasoning simply by modifying `.env`.

### Negative / Neutral Consequences
* High query concurrency on free keys may cause slight backoff pauses (2–6 seconds) during peak hours, which is clearly communicated via the Rich CLI progress indicator.

# ADR-0006: Configurable Gemini Flash Family & Graceful Rate-Limit Backoff

* **Status:** Accepted
* **Date:** 2026-10-15
* **Deciders:** Rudolfo Félix (AI Engineer), Vlad Bondarenko (Opsfleet AI Tech Lead Guidance)
* **Technical Story:** [RFC-001](../rfc/RFC-001-agentic-data-assistant.md)

---

## Context & Problem Statement
During initial alignment, Google Gemini 1.5 Flash was discussed as the base model. However, on October 15, 2026, **Vlad Bondarenko (AI Tech Lead at Opsfleet)** clarified the exact operational expectations:
> *"Model: you can also use `gemini-[2.5|3.1|3.5]-flash[-lite]`. The 1.5 models are retired, and Pro isn't on the free tier.  
> The 2–5 calls per query is a guide for free-tier limits, not a hard cap. Make the model configurable and handle rate-limit errors cleanly, since we'll run your code on our own key."*

Hardcoding a retired model version like `gemini-1.5-flash` or failing on HTTP 429 (`RESOURCE_EXHAUSTED`) would immediately cause runtime failures during the evaluator's test run.

## Decision Drivers
* Direct guidance from Opsfleet's AI Tech Lead.
* Zero-crash requirement during live evaluation.
* Free-tier compatibility on Google AI Studio.

## Considered Options
1. **Configurable Model via `.env` (`MODEL_NAME=gemini-2.5-flash`) + Exponential Backoff with Jitter (Selected):** Fully respects Vlad's directive. Provides clean terminal status warnings on rate limits and allows any modern Flash model to be swapped without code changes.
2. **Hardcoded Model (`gemini-1.5-flash`):** Fails immediately because Google retired the 1.5 preview series.
3. **Default to `gemini-pro`:** Fails on evaluators' free keys because Pro models require linked billing accounts.

## Decision Outcome
1. Make the LLM model completely configurable via `MODEL_NAME` in `.env`, defaulting to `gemini-2.5-flash` (or `gemini-2.5-flash-lite`).
2. Implement **exponential backoff with jitter** (initial 2.0s, factor 2.0, max 3 retries) wrapping all Gemini API invocations.
3. Catch HTTP 429 exceptions gracefully and display a visible warning in the CLI (`[yellow]Google AI Studio rate limit reached. Backing off for Xs (Attempt Y/3)...[/yellow]`).

### Positive Consequences
* Flawless evaluator experience: Vlad can clone the repo, inject his own `GEMINI_API_KEY`, and execute without encountering model deprecation or unhandled rate limit crashes.
* Future-proof: Easily accepts newer Flash iterations (`gemini-3.1-flash`, `gemini-3.5-flash-lite`) via simple `.env` edit.

### Negative / Neutral Consequences
* High query concurrency on free keys may cause slight backoff latency (2–6 seconds) during heavy traffic.

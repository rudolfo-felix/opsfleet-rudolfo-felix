# ADR-0001: Adopt LangGraph State Machine over Linear Chains

* **Status:** Accepted
* **Date:** 2026-10-15
* **Deciders:** Rudolfo Félix (AI Engineer), Vlad Bondarenko / Harry (Opsfleet PM Alignment)
* **Technical Story:** [RFC-001](../rfc/RFC-001-agentic-data-assistant.md)

---

## Context & Problem Statement
The assignment requires building an AI Data Assistant capable of handling complex conversational questions, executing BigQuery SQL queries, recovering from syntax/empty errors via a self-correction loop, and enforcing human confirmation on destructive commands. 
Traditional linear chains (e.g., standard LangChain `LLMChain` or basic sequential prompts) are strictly acyclic: they cannot loop back to retry queries without awkward recursive wrappers, lack native checkpointing, and cannot cleanly pause execution for human approval.

## Decision Drivers
* Need for cyclic state transitions (Self-correction loop: `bq_executor` $\rightarrow$ error $\rightarrow$ `self_correct` $\rightarrow$ `bq_executor`).
* Strict requirement for Human-In-The-Loop (HITL) interrupts for destructive operations.
* Requirement for typed, inspectable state (`AgentState`) rather than opaque string passing.
* Industry standard in 2025/2026 for production agent engineering.

## Considered Options
1. **LangGraph StateGraph (Selected):** Open-source cyclic graph with first-class checkpointers and interrupt primitives.
2. **Standard LangChain / LCEL:** Linear pipelines; requires custom while-loops outside the framework to handle retries.
3. **LlamaIndex Workflows:** Capable event-driven framework, but less natively aligned with Google AI Studio and Opsfleet's assessment hints.
4. **Custom Python Finite State Machine (FSM):** Complete control, but reinvents state checkpointing, streaming, and tool bindings from scratch.

## Decision Outcome
Adopt **LangGraph (`langgraph`)** as the primary orchestration engine.

### Positive Consequences
* Native support for cyclical execution (SQL self-correction retry loop capped at $\le 2$).
* Built-in `interrupt()` mechanics enabling EU AI Act Article 14 Human-In-The-Loop compliance.
* Seamless time-travel debugging and state inspection across nodes.
* 100% Open-Source (MIT License); runs locally or in Google Cloud Run at zero license cost.

### Negative / Neutral Consequences
* Slightly higher initial boilerplate (defining TypedDict states and node functions) compared to one-liner chains.

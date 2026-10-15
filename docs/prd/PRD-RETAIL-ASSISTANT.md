# Product Requirements Document (PRD)

## 📌 Retail Data Analysis AI Assistant
* **Project Name:** Retail Data Analysis Chat Assistant
* **Client / Stakeholder:** Retail Company Executive Leadership (Opsfleet Assessment Project)
* **Status:** Approved / Active
* **Version:** 1.0.0
* **Target Audience:** Non-technical Executive Teams (C-Level, Category Managers, VP of Retail)

---

## 🎯 1. Executive Summary & Problem Statement

### 1.1 The Business Problem
Executive leadership at modern retail enterprises struggles to extract real-time, actionable business insights from vast transactional data lakes. Currently, obtaining answers to strategic questions (e.g., *"Why did churn spike in California?"*, *"Which product departments yield the highest margins?"*) requires submitting support tickets to overwhelmed data engineering teams, resulting in days of latency.

### 1.2 The Proposed Solution
An **Agentic AI Conversational Data Assistant** that empowers non-technical executives to query enterprise data in natural language, automatically translates business questions into safe SQL, executes them against Google Cloud BigQuery (`thelook_ecommerce`), synthesizes strategic markdown reports with actionable next steps, and enforces strict corporate governance (PII masking and human-in-the-loop oversight).

---

## 👥 2. Target Personas & User Journeys

| Persona | Role | Key Goals & Needs | Primary Pain Points |
|---|---|---|---|
| **Sarah (CEO / VP)** | Chief Executive Officer | Macro-level business trends, executive summaries, strategic action items for Q1/Q2. | Lacks technical SQL knowledge; intimidated by raw databases; demands clean executive bullet points. |
| **Marcus (Category Director)** | Department Lead (e.g., Men/Women) | Product performance, inventory turnover, margin analysis scoped strictly to his brands. | Overwhelmed by irrelevant data; must not access competitor brand data (requires strict user scoping). |
| **David (Lead Data Analyst)** | Senior Data Analyst | Auditing generated SQL, verifying complex joins, promoting high-quality queries to Golden Bucket. | Constantly interrupted by routine ad-hoc questions; fears AI hallucinating inaccurate numbers. |

---

## 📋 3. Functional Requirements

### FR-1: Natural Language to BigQuery SQL Translation
* **Description:** The system must accept free-form business questions in natural language and generate valid GoogleSQL targeting `bigquery-public-data.thelook_ecommerce` (`orders`, `order_items`, `products`, `users`).
* **Acceptance Criteria:**
  - Accurately joins dimension and fact tables (e.g., `orders` $\leftrightarrow$ `order_items` $\leftrightarrow$ `products`).
  - Utilizes dynamic schema inspection rather than hardcoded column assumptions.
  - Generates analytical aggregations (SUM, AVG, COUNT DISTINCT, GROUP BY, ORDER BY).

### FR-2: Enterprise Safety & Data Minimization (PII Masking)
* **Description:** In compliance with GDPR and corporate privacy policies, executive users must never see raw Personally Identifiable Information (PII) on screen.
* **Acceptance Criteria:**
  - Columns `first_name`, `last_name`, `email`, and `ip_address` from table `users` must be scrubbed/redacted.
  - Final responses display masked tokens (e.g., `j***@example.com` or `[REDACTED_EMAIL]`).

### FR-3: User Scoping & Row-Level Authorization
* **Description:** Users must only analyze products and transactions related to their assigned portfolio.
* **Acceptance Criteria:**
  - Active user context (`user_id`, allowed brands/categories) is injected into queries as deterministic `WHERE` filters.
  - Cross-tenant data leaks are structurally prevented.

### FR-4: High-Stakes Oversight (Destructive Operations)
* **Description:** The assistant manages a "Saved Reports" library. Any request to delete reports (e.g., *"Delete all reports mentioning Brand X"*) must require explicit human confirmation.
* **Acceptance Criteria:**
  - The agent enters a paused state (Human-In-The-Loop Interrupt).
  - Explicit confirmation (`[y/N]`) must be provided by the executive before deletion is committed.

### FR-5: Autonomous Resilience & Error Auto-Fix
* **Description:** If a generated SQL query produces a BigQuery syntax error or an empty result, the agent must diagnose the issue and attempt self-correction.
* **Acceptance Criteria:**
  - Automatic retry loop capped at $\le 2$ attempts to protect FinOps budgets.
  - The UI must never crash with raw Python exception stack traces.

### FR-6: Executive Report Synthesis & Action Items
* **Description:** Raw SQL tabular results must be synthesized into an executive briefing.
* **Acceptance Criteria:**
  - Includes a concise summary, key numeric findings, and actionable recommendations for the upcoming quarter.

---

## ⚙️ 4. Non-Functional Requirements (NFRs)

* **NFR-1 (Usability & The 2-Minute Rule):** Evaluators must be able to clone the repository, supply a personal `GEMINI_API_KEY`, and run `python main.py` in under 2 minutes without missing dependencies or setup friction.
* **NFR-2 (FinOps, Model Configuration & Rate Limiting):** As specified by AI Tech Lead Vlad Bondarenko:
  - Model must be configurable via `MODEL_NAME` (defaulting to `gemini-2.5-flash`, swappable to `gemini-2.5-flash-lite` or `gemini-3.1-flash`). Retired 1.5 models and paid Pro models are strictly excluded.
  - LLM call budget per analytical question is guided to **2–5 calls** to protect free-tier quotas.
  - HTTP 429 (`RESOURCE_EXHAUSTED`) exceptions must be intercepted with exponential backoff and jitter, providing user-visible CLI feedback without crashing.
* **NFR-3 (Regulatory Alignment):** Designed in alignment with **EU AI Act (Article 14 - Human Oversight)** and **NIST AI RMF (GOVERN, MAP, MEASURE, MANAGE)**.
* **NFR-4 (Portability & Free-Tier First):** Zero proprietary vendor lock-in. 100% runnable at $0.00 cost on Google AI Studio Free Tier and open-source packages.

---

## 🚫 5. Out of Scope (Non-Goals for Prototype)

* Multi-tenant microservices deployment (addressed in HLD).
* Distributed vector database clusters (addressed in HLD).
* Direct web dashboard frontend (CLI interface is the agreed delivery mechanism).

# AI Technical Assignment: Retail Company

**Client:** Retail Company (Opsfleet is the client for this project; Team Lead + Harry are the Project Managers)  
**Target Audience:** Non-technical Executive Teams  
**Slack Canvas:** [AI Technical Assignment - Retail Company](https://opsfleet.slack.com/docs/T38KZJ5AM/F0A9MTCMS20)

---

## The Challenge: Design and Build a Data Analysis Chat Assistant
You are building a data analysis agent for a Retail Company's non-technical executive teams. These executives need to ask complex questions about sales and performance naturally:
- *"Why are the users for state X underspending? And how does it compare to users in state Y?"*
- *"Why did our churn rate spike last month?"*
- *"Create a report for Q1 including insights and action items for Q2."*

### Assets Available:
* **The Database:** A read-only connection to a SQL database containing raw transaction logs: Google Cloud BigQuery dataset `bigquery-public-data.thelook_ecommerce` (`orders`, `order_items`, `products`, `users`).
* **The "Golden Knowledge" Bucket:** A data lake containing historical "Trios" (*Question $\rightarrow$ SQL Query $\rightarrow$ Analyst Report*) created by human experts (Theoretical).

---

## Deliverables Required
1. **Architecture Diagram (Mermaid, etc.):** Highlighting building blocks, services, compute, and flow based on all requirements.
2. **Detailed Technical Explanation:**
   - Reasoning for chosen Cloud services / LLM models / frameworks.
   - Data flow between components.
   - Error handling and fallback strategies.
   - Setup instructions and example run.
   - Detailed explanation of how each requirement is solved in production.
3. **Working Code / Prototype:** Build a chat agent that allows users to ask data-related questions naturally, discuss them, and create reports with action items.
   - **Supported Prototype Requirements:**
     - *a. Safety & PII Masking*
     - *b. High-Stakes Oversight (Destructive Ops with confirmation)*
     - *c. Resilience & Graceful Error Handling (Self-correcting SQL loop)*
     - *d. Observability*
4. **CLI-based Interface:** Clean terminal chat interactions.
5. **Runnable on Another Machine:** Proper setup instructions and virtual environment configuration.
6. **Framework Choice:** Use a framework of your choice (LangGraph), explain why you chose it, and your level of experience.

---

## Detailed Requirements Summary
1. **Hybrid Intelligence:** Explain how to use and update the "Golden Bucket" over time and provide relevant few-shot data at query time.
2. **Safety & PII Masking:** Strictly forbidden from displaying raw PII (names, emails, IPs) in the final output. Row-level product scoping per user.
3. **High-Stakes Oversight (Destructive Ops):** Manage a "Saved Reports" library. Inputs like *"Delete all reports mentioning Client X"* require a strict confirmation flow before execution.
4. **Continuous Improvement (The Learning Loop):** User-level preference learning (tables vs bullets, analysis depth) and system-level self-improvement.
5. **Resilience & Graceful Error Handling:** Detect syntax errors or empty returns and attempt to self-correct before giving up, without UI crashes or cost inflation.
6. **Quality Assurance:** Strategy for pre-deployment evaluations, user intent verification, and UX evaluation.
7. **Observability:** Agent-level metrics tracking and deep-dive debugging support.
8. **Agility (Persona Management):** Allow non-developers (e.g., CEO) to update report tone weekly without redeployments.

---

## Time Expectation & Submission
* **Time Expectation:** 6 to 12 hours of work.
* **Submission:** Public GitHub repository shared in the Slack channel `#t-ai-rudolfo-félix`.

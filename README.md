# Opsfleet AI Technical Assignment: Retail Data Analysis Chat Assistant

**Candidate:** Eng. Rudolfo Valentino Marques Félix  
**Position:** AI Engineer (Opsfleet)  
**Repository:** [github.com/rudolfo-felix/opsfleet-rudolfo-felix](https://github.com/rudolfo-felix/opsfleet-rudolfo-felix)  
**Slack Channel:** `#t-ai-rudolfo-félix`

---

## 📖 Overview

This repository contains the complete submission for the Opsfleet AI Technical Assessment. 
The objective is to design a production-ready **High-Level Design (HLD)** and build an elegant, runnable **CLI-based Data Analysis Chat Assistant Prototype** for non-technical retail executive teams, leveraging Google Cloud BigQuery (`bigquery-public-data.thelook_ecommerce`) and Google Gemini.

---

## 📂 Repository Contents & Documentation

* 📑 **[Master Execution Plan & Checklist](docs/MASTER_PLAN.md):** Complete operational plan, Slack Q&A alignment with Harry (AI PM) & Vlad (AI Tech Lead), **Architectural Trade-offs Table**, and granular verification checklist.
* 🏛️ **C4 Architectural Standard:** HLD structured following the **C4 Model (Level 2 Container & Level 3 Component)** mapped to Google Cloud Platform managed services.
* 📄 **[Official Assignment Specification (Markdown)](docs/ASSIGNMENT_SPEC.md):** Markdown version of the retail company challenge.
* 📄 **[Opsfleet AI Engineer Job Description (Markdown)](docs/JOB_DESCRIPTION.md):** Full role specification and core responsibilities.
* 📚 **Architectural Foundations & Reference Whitepapers:**
  * [The Agentic Operating Model (LangChain Whitepaper)](docs/The%20Agentic%20Operating%20Model.pdf) — Enterprise blueprint for the Agent Development Lifecycle (ADLC), LangGraph stateful execution, HITL interrupts, and agentic governance.
* 📦 **Original Assessment PDFs:**
  * [AI Technical Assignment - Retail Company.pdf](docs/AI%20Technical%20Assignment%20-%20Retail%20Company.pdf)
  * [AI Engineer Opsfleet.pdf](docs/AI%20Engineer%20Opsfleet.pdf)

---

## 🚀 Quick Links & Direct References

* 📄 **Slack Canvas Document:** AI Technical Assignment - Retail Company (Opsfleet Candidate Canvas)
* 💬 **Opsfleet Slack Channel:** `#t-ai-rudolfo-félix`
* 🗄️ **BigQuery Target Dataset:** `bigquery-public-data.thelook_ecommerce` (`orders`, `order_items`, `products`, `users`)
* 🤖 **LLM Engine:** Google Gemini (`gemini-1.5-flash`) via [Google AI Studio](https://aistudio.google.com/)

---

## 🛠️ Implementation Progress

- [x] Repository created and synchronized on GitHub (`rudolfo-felix/opsfleet-rudolfo-felix`).
- [x] Initial documentation, PDFs, and master execution plan added.
- [ ] Phase 1: Environment & BigQuery Client setup.
- [ ] Phase 2: LangGraph State Machine & self-correction retry loop.
- [ ] Phase 3: PII Masking & Product Scoping guardrails.
- [ ] Phase 4: Saved Reports Library & destructive operations confirmation flow.
- [ ] Phase 5: Rich CLI interactive interface & Observability traces.
- [ ] Phase 6: Final HLD Architecture Diagram (`docs/HLD.md`) & submission.

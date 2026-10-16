# 🛡️ Model Allocation, Enterprise Failure Resilience & Genesis Prompt
**Author:** L8 Principal Systems Architect & AI Engineering Auditor  
**Repository:** `/Users/rudy/Documents/opsfleet-rudolfo-felix`  
**Date:** 2026-10-16  

---

## 🤖 1. Reviewed Model Allocation & FinOps Plan

### Token & Model Availability Context
* **Antigravity State:** Claude Sonnet 4.6, Claude Opus 4.6, and GPT-OSS 120B are in a **4h41m cooldown/rate-limit period**.  
  **Active Model in Antigravity:** **Gemini 3.8 Flash (High)** is available with ample capacity.
* **Codex CLI State:** Authenticated, trusted, with **81% quota remaining** (`codex-cli 0.163.0` verified at `~/.local/bin/codex`), with the newly updated model suite from `~/.codex/models_cache.json`:
  - `gpt-6-luna` (fast, efficient, official migration successor to `gpt-5.4-mini`)
  - `gpt-5.6-terra` (balanced multi-file engineering model, default in `~/.codex/config.toml`, successor to `gpt-5.5`)
  - `gpt-5.6-luna` (high-capacity reasoning model for complex state machines & reflection)
  - `gpt-reserve` (dedicated agentic coding fallback model)
  - `codex-auto-review` (automated reviewer model)
* **Antigravity CLI (`agy`):** Shares the same Antigravity account and model quotas as the IDE. Because Claude and GPT-OSS are rate-limited on Antigravity, `agy` does not unlock them. Therefore, **Codex CLI is our primary execution engine for code**, while Antigravity with **Gemini 3.8 Flash** acts as our **First Mate / Orchestrator / Documentation Engine**.

### Ticket-by-Ticket Model Allocation:

| Ticket / Milestone | Recommended Model | Reasoning Effort | Execution Engine | Est. Quota Cost | L8 Architectural Rationale |
|---|---|:---:|:---:|:---:|---|
| **OPS-001** (Scaffolding, Pydantic, Backoff) | `gpt-6-luna` | `medium` | Codex CLI | ~2% | Boilerplate determinístico: Pydantic BaseSettings, `.env.example`, `resilience.py` decorator e `conftest.py`. Rápido e ultra econômico. |
| **OPS-002A** (BigQuery Live Client & Cache) | `gpt-5.6-terra` | `medium` | Codex CLI | ~4% | Introspecção do `INFORMATION_SCHEMA`, TTL cache em memória e sanitizador de tabelas. |
| **OPS-002B** (DuckDB Mock & Dialect Adapter) | `gpt-5.6-terra` | `high` | Codex CLI | ~6% | Requer regex adapter para traduzir GoogleSQL (`TIMESTAMP_SUB`, `DATE_TRUNC`, `SAFE_DIVIDE`, backticks) para DuckDB e gerar fixtures de 50+ rows. |
| **OPS-003** (AgentState, Prompts & SQL Gen) | `gpt-5.6-terra` | `high` | Codex CLI | ~6% | Modelagem de TypedDict, strip determinístico de code fences e regras ontológicas ONT-001 (Net Revenue, Churn). |
| **OPS-004** (Execution, Self-Correction & Graph) | `gpt-5.6-luna` | `high` | Codex CLI | ~10% | O grafo LangGraph é o núcleo do sistema: Intent Router condicional, reflection loop de auto-cura, circuit breaker ($\le 2$) e diagnóstico de 0-rows. Luna possui raciocínio superior para fluxos cíclicos de controle. |
| **OPS-005** (Executive Synthesizer Node) | `gpt-5.6-terra` | `medium` | Codex CLI | ~5% | Síntese executiva formatada em 3 seções H2 para Sarah (CEO), PII-safe consumindo `sanitized_results`. |
| **OPS-006** (Enterprise PII & Brand Scoping) | `gpt-6-luna` | `high` | Codex CLI | ~4% | Implementação in-process com regex e Presidio (sem downloads pesados de spaCy) e scoping condicional de marcas. |
| **OPS-007** (SQLite Reports & HITL Interrupt) | `gpt-5.6-terra` | `medium` | Codex CLI | ~5% | Persistência SQLite (`reports.db`), `MemorySaver` com session `thread_id` UUID e `interrupt()` para exclusão segura. |
| **OPS-008** (OTel GenAI Tracing & Token Tracker) | `gpt-6-luna` | `medium` | Codex CLI | ~3% | Spans CNCF `gen_ai.*`, tracking de latência e orçamento de 2–5 chamadas LLM. |
| **OPS-009** (Rich CLI & Application Entrypoint) | `gpt-5.6-terra` | `medium` | Codex CLI | ~6% | Terminal Rich, spinners, tabelas auto-truncadas, flags `--dry-run` e loop de chat com HITL. |
| **OPS-010 Part A** (Production HLD Document) | **Gemini 3.8 Flash (High)** | Deep Context | **Antigravity** | **0% Codex** | Antigravity gera o `docs/HLD.md` completo com os diagramas Mermaid C4 diretamente. Zero gasto de quota no Codex! |
| **OPS-010 Part B** (`scripts/verify_batteries.py`) | `gpt-5.6-terra` | `medium` | Codex CLI | ~5% | Script automatizado que roda os testes das 20 baterias (TB-01 a TB-17) e valida os checklists (TB-18 a TB-20). |
| **Adversarial Final Audit** (3x Verification) | `gpt-5.6-luna` | `high` | Codex CLI | ~8% | Auditoria final simulando avaliador cego com injeções maliciosas e verificação de integridade de links. |
| **TOTAL ESTIMADO** | | | | **~59%** (de 81%) | **Margem de Segurança: ~22% de folga** para correções. |

---

## 🏛️ 2. Enterprise Failure Resilience & High-Availability Architectural Mapping

Mapeamos os 6 pilares de resiliência corporativa e tolerância a falhas diretamente para a arquitetura do nosso assistente:

```
+---------------------------------------------------------------------------------------------------+
|                                HOW TO DESIGN FOR FAILURE                                         |
+---------------------------------------------------------------------------------------------------+
| 1. FAULT AVOIDANCE vs TOLERANCE  | Avoid: Strict Typing, Pydantic, Code Review                   |
|                                  | Tolerate: Failover (DuckDB Mock), Checkpoint (MemorySaver)     |
|----------------------------------+----------------------------------------------------------------|
| 2. CELL-BASED ARCHITECTURE       | Tenant/Brand Isolation (Marcus: Calvin Klein vs Tommy Hilfiger)|
|                                  | Minimizes Blast Radius if a tenant query fails                |
|----------------------------------+----------------------------------------------------------------|
| 3. DATABASE REPLICATION          | SQLite Local (Sync ACID writes) vs BQ/Lakehouse (Async ETL)   |
|----------------------------------+----------------------------------------------------------------|
| 4. RETRIES, BACKOFF & JITTER     | Jittered Backoff on HTTP 429 & 503; Cap Attempts <= 2         |
|                                  | Never Retry Bad Input (Route to Self-Correction Node)          |
|----------------------------------+----------------------------------------------------------------|
| 5. BACKPRESSURE & LOAD SHEDDING  | FinOps Budget (2-5 calls/query); Circuit Breaker sheds load   |
|----------------------------------+----------------------------------------------------------------|
| 6. RTO vs RPO                    | RTO < 2 min (2-Minute Evaluator Rule); RPO = 0 (SQLite Sync)   |
+---------------------------------------------------------------------------------------------------+
```

### 1. Fault Avoidance vs. Fault Tolerance
* **Fault Avoidance (Antes do Incidente):**
  - Tipagem 100% estrita com Pydantic `BaseSettings` (`src/config.py`).
  - Auditoria adversarial em janela de contexto limpa por subagentes antes de qualquer merge.
  - Pré-commit scripts checando story linkage e integridade de links.
* **Fault Tolerance (Depois do Incidente):**
  - **Failover:** Se as credenciais do Google Cloud ADC falharem, o `DualBigQueryClient` faz failover transparente para o motor `MockDuckDBEngine` em memória. Zero crash `DefaultCredentialsError`.
  - **Resume from Checkpoint:** Se o usuário interrompe uma exclusão de relatório, o `MemorySaver` preserva o estado na sessão e retoma a partir do checkpoint exato.
  - **Degraded Response:** Se uma consulta retorna 0 linhas, o sistema não crasha; emite diagnóstico construtivo de casing e filtros de data (Mitigação 3).

### 2. Cell-Based Architecture (Contenção de Blast Radius)
* Na arquitetura de produção (HLD C4 Container), as consultas e limites de quota são particionadas por **Células de Tenant / Marca** (ex: Célula Calvin Klein vs. Célula Tommy Hilfiger).
* Se um Category Director disparar consultas pesadas que atinjam o rate-limit da API, o blast radius fica confinado à sua célula de marca, sem impactar outros executivos ou a CEO Sarah.

### 3. Database Replication & State Separation
* **Escritas Síncronas:** Operações de persistência de relatórios executivos no SQLite (`reports.db`) utilizam transações ACID síncronas locais (RPO = 0, sem perda de briefings salvos).
* **Leituras Analíticas:** O BigQuery e o DuckDB funcionam como réplicas analíticas desacopladas do armazenamento transacional de relatórios.

### 4. Retries, Backoff & Jitter
* Conforme ilustrado nos padrões de resiliência corporativa:
  $$\text{Wait} = \text{InitialDelay} \times (\text{Factor})^{\text{attempt}} \pm \text{Jitter}$$
* **O que retentar:** Erros transitórios de rede, HTTP 503 e HTTP 429 (`RESOURCE_EXHAUSTED`).
* **O que NÃO retentar:** Bad input (erros de sintaxe SQL ou parâmetros inválidos). Erros de SQL nunca são reenviados diretamente à rede; são roteados para o nó de reflexão (`self_correct`) com contagem determinística de tentativas.
* **Cap Attempts:** Máximo de 3 tentativas na camada de rede (`@retry_with_backoff`) e máximo estrito de 2 tentativas no loop de SQL do LangGraph (Circuit Breaker).

### 5. Backpressure & Load Shedding
* **Bounded Budget:** Orçamento rígido de **2 a 5 chamadas LLM por pergunta**, guiado pelo Vlad.
* **Load Shedding:** Se o contador de retentativas atingir o limite (`retry_count == 2`), o circuit breaker corta imediatamente novas chamadas ao modelo e descarta trabalho excedente, devolvendo uma resposta executiva educada.
* **Backpressure na CLI:** Se a API do Google AI Studio entrar em cooldown, a CLI Rich renderiza uma contagem decrescente visual, impedindo o usuário de bombardear o backend.

### 6. RTO vs. RPO
* **RTO (Recovery Time Objective):** `< 2 minutos` — A regra sagrada do avaliador. Qualquer falha de ambiente é recuperada instantaneamente via DuckDB e fallback determinístico.
* **RPO (Recovery Point Objective):** `0 segundos` para dados do usuário (SQLite com WAL mode) e tolerância configurável para caching de schemas de BigQuery (TTL = 3600s).

---

## 📋 3. Revisão da Checklist Completa (Triple Verification Protocol)

Todas as 20 baterias (TB-01 a TB-20) devem ser testadas em 3 passagens antes da entrega final:
- **Pass 1:** Verificação local durante o desenvolvimento de cada ticket.
- **Pass 2:** Clean-room dry run num ambiente venv virgem (`python -m venv .venv_clean`).
- **Pass 3:** Simulação adversarial com injeções maliciosas e edge cases do avaliador.

### Matriz de Baterias:
1. **TB-01:** Clone cego em < 45s com `pip install -e .` sem erros de compilação.
2. **TB-02:** Injeção de chave do avaliador no `.env` sem crashes.
3. **TB-03:** Modo BigQuery Live em `bigquery-public-data.thelook_ecommerce`.
4. **TB-04:** Modo BigQuery Offline / Mock DuckDB (zero GCP setup).
5. **TB-05:** Consulta de Net Revenue (enforçando status NOT IN 'Cancelled', 'Returned').
6. **TB-06:** Consulta de Churn trailing 90 dias (sem falhar em coluna inexistente).
7. **TB-07:** Consulta de AOV e Margem com joins em `products` e `SAFE_DIVIDE`.
8. **TB-08:** Ataque direto de PII (mascaramento de emails e IPs).
9. **TB-09:** Prompt Injection / Jailbreak (redação in-process fora do LLM).
10. **TB-10:** Scoping de marca (Marcus limitado às suas marcas).
11. **TB-11:** Salvamento e listagem de relatórios no SQLite.
12. **TB-12:** Aborto de exclusão destrutiva (`[N]` preserva relatório).
13. **TB-13:** Confirmação de exclusão destrutiva (`[y]` purga relatório).
14. **TB-14:** Auto-correção de erro de sintaxe SQL pelo nó de reflexão.
15. **TB-15:** Disparo do Circuit Breaker em $\le 2$ tentativas sem loop infinito.
16. **TB-16:** Backoff com jitter em HTTP 429 sem unhandled tracebacks.
17. **TB-17:** Orçamento FinOps de 2–5 chamadas LLM respeitado.
18. **TB-18:** Renderização 100% legível dos diagramas Mermaid C4 no GitHub.
19. **TB-19:** 100% dos links de documentação resolvidos sem erros 404.
20. **TB-20:** Git tree limpa e commits com story linkage (`OPS-XXX feat: ...`).

---

## ⚡ 4. The Master Genesis Setup Prompt (Template Reutilizável)

Este é o prompt mestre para inicializar do zero qualquer projeto ou avaliação técnica de IA com nível de rigor **L8 Principal Engineer**:

```markdown
You are an L8 Principal Systems Architect and Staff AI Engineer.
You operate under the "Captain & Crew" agent engineering framework: hands-on-keyboard terminal focus, progressive disclosure, anti-fragility, and evidence-based quality gates.

I am initializing an enterprise AI Agent repository for [PROJECT_NAME / ASSESSMENT_NAME].
The core business objective is: [ONE_SENTENCE_GOAL].
The key personas and stakeholders are: [PERSONAS].
The technical constraints, evaluator requirements, and directives are:
- [CONSTRAINT 1: e.g. Model configurability, API limits, 2-minute clone-and-run rule]
- [CONSTRAINT 2: e.g. Dual-engine live + offline mock fallback]
- [CONSTRAINT 3: e.g. Zero external PII egress, EU AI Act Article 14 human-in-the-loop]

Execute Phase 0 (Groundwork & Architecture) before writing any application code:

1. ARCHITECTURAL INVARIANTS (AGENTS.md):
   Create a root `AGENTS.md` defining the 10+ immutable engineering invariants of the repo:
   - 2-Minute Evaluator Rule (zero compilation or credential crashes out of the box).
   - Rate limit resilience (exponential backoff with jitter on HTTP 429/503).
   - Call budget discipline (strict cap on LLM invocations per query).
   - Dual-engine strategy (live cloud provider + offline in-memory mock engine).
   - Evidence-based verification gate (every task must save real pytest/fixture outputs to tests/evidence/).
   - Zero development-cost bias (enterprise patterns: Pydantic BaseSettings, explicit error hierarchies, typing).

2. DOMAIN-DRIVEN DESIGN & ONTOLOGY:
   Create `docs/architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md` establishing the ubiquitous language, deterministic calculation rules (e.g. Net Revenue excluding returns, Churn definitions), and avoiding LLM semantic hallucinations.

3. ARCHITECTURE DECISION RECORDS (ADRs):
   Create `docs/adr/` with numbered ADRs (ADR-0001 to ADR-0007) documenting architectural trade-offs:
   - State machine / orchestration choice (LangGraph cyclic graph vs linear chains).
   - Observability & Tracing (vendor-neutral OpenTelemetry / Langfuse OSS vs proprietary SaaS).
   - Storage strategy (local zero-install SQLite for prototype vs Cloud SQL for HLD).
   - In-process PII redaction vs Cloud DLP (latency, cost, data sovereignty).
   - Model configurability & FinOps trade-offs.

4. TECHNICAL SPECIFICATION (RFC-001):
   Create `docs/rfc/RFC-001-[feature-name].md` detailing the complete StateGraph, TypedDict AgentState schema, node-by-node input/output contracts, and circuit breaker logic.

5. ATOMIC DELIVERY BACKLOG (tickets/):
   Decompose the roadmap into strictly sized, atomic tickets (OPS-001 to OPS-XXX) in `tickets/`:
   - Each ticket must have: Overview, Goal, Description, Testable Acceptance Criteria, and Completion Criteria.
   - Decouple tickets so an autonomous agent can execute them in isolation with < 2,500 tokens of context.
   - Build a visual Mermaid Execution DAG in `tickets/README.md`.

6. TRIPLE VERIFICATION PROTOCOL & TEST BATTERIES:
   In `docs/MASTER_PLAN.md`, define a comprehensive battery of 20 evaluation scenarios (TB-01 to TB-20) covering:
   - Blind clone & packaging.
   - Live cloud mode vs. offline mock engine.
   - Business metric precision queries.
   - PII attacks and prompt injection defense.
   - Human-in-the-loop pause/resume confirmation flows.
   - Self-correction loops and circuit breaker caps.
   - 3x Pass Verification Matrix: Pass 1 (Dev), Pass 2 (Clean venv), Pass 3 (Adversarial simulation).

Do NOT write production application code yet. First deliver the complete, verified documentation suite and ticket backlog with 100% link resolution and zero broken paths.
```

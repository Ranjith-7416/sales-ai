# Sales AI — System Architecture & Interview Preparation Guide

This comprehensive guide breaks down the core architecture, design decisions, trade-offs, and common interview questions for the **Agentic AI Sales Lead Qualification & Proposal Generation System**.

---

## 1. Executive Summary & Problem Statement

### The Problem
Enterprise sales teams spend over **60% of their time** on manual, non-selling administrative tasks:
- Manually researching prospective companies across public websites and registries
- Parsing unstructured customer emails and multi-page Request for Proposal (RFP) PDFs
- Manually checking if customer requirements match existing product/service offerings
- Calculating qualification scores and drafting customized commercial proposals

### The Solution: Sales AI
Sales AI is an **Agentic Multi-Agent Pipeline** that automates the entire sales qualification lifecycle:
1. Ingests raw text inquiries or multi-page RFP documents (PDF, DOCX, TXT)
2. Researches the prospect's company background, industry vertical, and scale
3. Extracts functional requirements, technical constraints, and missing information
4. Concurrently matches requirements against catalog solutions (RAG) and scores lead viability
5. Drafts a complete, grounded, multi-tier commercial proposal
6. Audits the proposal using an independent critic agent before human sales rep review

---

## 2. High-Level System Architecture

```
[ Customer Inquiry / RFP (PDF/DOCX) ]
                 │
                 ▼
     [ FastAPI Ingestion API ] ──► [ BackgroundTasks Worker ]
                 │
                 ▼
       ┌────────────────────────────────────────────────────────┐
       │             LangGraph Multi-Agent Pipeline             │
       │                                                        │
       │  1. [ Lead Research Agent ]                            │
       │           │                                            │
       │           ▼                                            │
       │  2. [ Requirements Analysis Agent ]                    │
       │           │                                            │
       │           ▼ (asyncio.gather - Fan-Out)                 │
       │     ┌────────────────────────────────────┐             │
       │     │                                    │             │
       │  3a. [ Qualification Agent ]      3b. [ Solution Agent ]│
       │      (Deterministic Scoring)         (ChromaDB RAG)    │
       │     │                                    │             │
       │     └────────────────────────────────────┘             │
       │           │ (Fan-In)                                   │
       │           ▼                                            │
       │  4. [ Proposal Generation Agent ]                      │
       │           │                                            │
       │           ▼                                            │
       │  5. [ Reviewer Agent (Actor-Critic Auditor) ]          │
       │           │                                            │
       │           ▼                                            │
       │  6. [ Terminal State / DB Persistence ]                │
       └────────────────────────────────────────────────────────┘
                 │
                 ▼
       [ SQLite / PostgreSQL ] ◄─── [ React + Vite UI Dashboard ]
```

---

## 3. Core Architectural Decisions (The "Why")

### Q1: Why use LangGraph instead of standard LangChain chains or AutoGen/CrewAI?
* **State Machine Predictability**: In B2B enterprise workflows, unstructured agent autonomy (like AutoGen agents chatting indefinitely) leads to unpredictable token loops, excessive latency, and unbudgeted API bills.
* **LangGraph `StateGraph`**: Models execution as an explicit directed acyclic graph (DAG). State is shared immutably via `PipelineState` and validated at each step using Pydantic.
* **Latency Optimization (Fan-Out/Fan-In)**: The Qualification Agent and Solution Matching Agent are logically independent. We run them concurrently using `asyncio.gather`, cutting pipeline latency by ~40%.
* **Fault Isolation**: Each node wraps its execution in isolated try/catch blocks. If web search fails during Research, the pipeline degrades gracefully instead of crashing.

---

### Q2: Why use a Deterministic Python Scoring Engine instead of asking the LLM to score?
* **The Hallucination & Consistency Problem**: LLM token sampling is inherently non-deterministic. Prompting an LLM with *"Score this lead from 1 to 100"* causes the same enterprise inquiry to score 85 on Monday and 48 on Tuesday.
* **Enterprise Compliance & Auditability**: Regulated enterprise customers require 100% explainability. Sales directors must be able to justify to leadership why a lead was tagged "Qualified" or "Low Priority".
* **Separation of Concerns**:
  * **LLM Role (Qualitative)**: Semantic understanding of unstructured natural language (extracting budgets, volumes, timelines, and constraints).
  * **Python Engine Role (Quantitative)**: Mathematical linear weighting, bounds checking, and rule-based threshold comparison.

#### The Authoritative 4-Pillar Formula:
$$\text{Composite Score} = (0.25 \times \text{Fit}) + (0.25 \times \text{Readiness}) + (0.30 \times \text{Opportunity}) + (0.20 \times (100 - \text{Risk}))$$

1. **Solution Fit (25%)**: Semantic match against Document AI, Customer Support, and Compliance catalog items.
2. **Readiness (25%)**: Budget availability and project deployment timeline urgency.
3. **Opportunity Scale (30%)**: Monthly operational volume (e.g., 10,000+ PDFs/month awards +40 points) and organization employee count.
4. **Commercial Risk (20%)**: Missing critical requirements, ambiguity, or non-commercial consumer requests.

#### Decision Thresholds:
- **$\ge 75.0$**: 🟢 **Qualified** (Fast-track to proposal generation)
- **$50.0 \text{ to } 74.9$**: 🟡 **Needs More Information** (Prompts sales rep with targeted follow-up questions)
- **$< 50.0$**: 🔴 **Low Priority** (Disqualifies non-viable/hobby requests)

---

### Q3: How does RAG work in this system, and how do you guarantee solution grounding?
* **Dense Vector Indexing**: Product and service catalogs (`products.json` and `services.json`) are converted into vector embeddings using `sentence-transformers` (`all-MiniLM-L6-v2`) and stored in ChromaDB collections.
* **Semantic Retrieval**: Cosine similarity search retrieves the top-k most relevant offerings based on customer inquiry requirements.
* **Grounding Check (Anti-Hallucination)**:
  - Generative LLMs often promise features that the vendor does not sell.
  - The Solution Agent computes an explicit `grounding_validation` metric.
  - The Proposal Agent is constrained by system prompts to only reference products present in the retrieved context.
  - The Reviewer Agent audits every proposal claim against the catalog to verify that all referenced features are grounded.
* **Offline Fallback**: If ChromaDB or the model weights cannot load, the system falls back to a deterministic keyword-matching engine, guaranteeing 100% API uptime.

---

### Q4: Why use the Actor-Critic pattern with the Reviewer Agent?
* **Generative Over-Optimism**: When an LLM acts as the Proposal Generator ("Actor"), it exhibits confirmation bias—it assumes its own solution is flawless.
* **Independent Auditor ("Critic")**: The Reviewer Agent operates with an adversarial system prompt. It analyzes:
  - **Requirement Coverage**: Did the proposal address every must-have item?
  - **Budget Alignment**: Does the pricing proposal exceed the client's stated budget?
  - **Risk Assessment**: Are there implementation or margin risks?
* **Output**: Produces an explicit `approval_status` ("Approved", "Approved with Conditions", "Needs Revision") and generates follow-up questions for the sales rep.

---

### Q5: How is the backend engineered for production concurrency and resilience?
1. **Asynchronous Background Decoupling**:
   - Multi-agent pipelines take 10–25 seconds.
   - Synchronous HTTP endpoints would block ASGI workers and trigger client HTTP timeouts (e.g. 30s gateway limits).
   - `POST /api/leads` immediately writes the lead to the DB with status `processing`, returns HTTP 200/202 with `lead_id`, and runs the orchestrator via FastAPI `BackgroundTasks`.
2. **Quota Circuit Breaker (Fail-Fast Pattern)**:
   - Differentiates between transient network errors (503/502 retried with exponential backoff) versus permanent quota exhaustion (429 daily quota depleted).
   - Raises `ProviderQuotaError` to instantly cut off further pipeline calls, preventing billing spikes and latency hangs.
3. **Database Connection Pool Tuning**:
   - `pool_pre_ping=True`: Validates connections with a lightweight ping to recover from dropped firewall sockets.
   - `pool_size` and `max_overflow`: Prevents exhausting database server file descriptors under traffic surges.
   - `yield db` in `get_db()`: Guarantees connection release via `finally: db.close()`.
4. **Security & Defense-in-Depth**:
   - JWT authentication (`require_auth`) protects all sensitive endpoints.
   - Passwords hashed using `bcrypt` (never stored in plaintext).
   - Redis-backed rate limiting protects expensive AI endpoints against denial-of-wallet attacks.

---

## 4. Quick Reference: Key Code Locations

| Component | File Path | Key Responsibilities |
| :--- | :--- | :--- |
| **Orchestrator** | [`backend/app/agents/orchestrator.py`](file:///Users/ranjithkumar/Desktop/sales-ai/backend/app/agents/orchestrator.py) | LangGraph StateGraph, parallel fan-out/fan-in, schema validation |
| **Scoring Engine** | [`backend/app/services/scoring_engine.py`](file:///Users/ranjithkumar/Desktop/sales-ai/backend/app/services/scoring_engine.py) | Deterministic 4-pillar scoring formula, threshold boundaries |
| **RAG Service** | [`backend/app/services/rag_service.py`](file:///Users/ranjithkumar/Desktop/sales-ai/backend/app/services/rag_service.py) | ChromaDB vector search, embeddings, offline fallback |
| **LLM Service** | [`backend/app/services/llm_service.py`](file:///Users/ranjithkumar/Desktop/sales-ai/backend/app/services/llm_service.py) | Multi-provider abstraction, fail-fast quota circuit breaker |
| **Reviewer Agent** | [`backend/app/agents/reviewer_agent.py`](file:///Users/ranjithkumar/Desktop/sales-ai/backend/app/agents/reviewer_agent.py) | Actor-Critic auditor, compliance verification, approval status |
| **Leads API** | [`backend/app/api/leads.py`](file:///Users/ranjithkumar/Desktop/sales-ai/backend/app/api/leads.py) | FastAPI routes, BackgroundTasks decoupling, rate limiting |
| **Database Pool** | [`backend/app/database.py`](file:///Users/ranjithkumar/Desktop/sales-ai/backend/app/database.py) | SQLAlchemy engine pooling, session lifecycle generator |

---

## 5. Top 10 Technical Interview Questions & Model Answers

### 1. "Can you walk me through the lifecycle of a lead in your system?"
> *"When a customer inquiry or RFP document is submitted via the UI, the FastAPI backend immediately validates the schema, persists the initial record in SQLite/PostgreSQL with status `processing`, and delegates execution to a background worker. 
> The worker initializes a LangGraph StateGraph. The Research Agent first gathers company context. Next, the Requirements Agent extracts structured functional needs and missing information. 
> Then, the pipeline fans out concurrently: the Qualification Agent computes a deterministic score (Fit, Readiness, Opportunity, Risk), while the Solution Agent queries ChromaDB via RAG to retrieve matching product catalog items. 
> The Proposal Agent synthesizes this grounded data into a draft proposal. Finally, the Reviewer Agent performs an Actor-Critic audit to check compliance, pricing, and risk before saving the finalized results to the database for sales rep review."*

---

### 2. "Why did you choose LangGraph over traditional LangChain chains?"
> *"Traditional LangChain chains are predominantly linear and stateless. In contrast, enterprise sales qualification is an iterative state machine with branching logic, parallel execution, and strict error recovery. 
> LangGraph allows us to define nodes as isolated async functions sharing a single typed `PipelineState`. Crucially, it enabled us to execute the Qualification Agent and Solution Matching Agent in parallel using `asyncio.gather`, cutting pipeline latency by ~40% while isolating faults so that a failure in one stage doesn't crash the entire pipeline."*

---

### 3. "How do you prevent the LLM from hallucinating lead scores?"
> *"We do not allow the LLM to calculate scores. We enforce a strict separation of concerns: the LLM is only used for qualitative semantic extraction—identifying unstructured attributes such as budget numbers, monthly document volume, and timeline urgency. 
> Those extracted attributes are then fed into a purely deterministic Python scoring engine that applies mathematical formulas with strict weights (25% Fit, 25% Readiness, 30% Opportunity, 20% Risk). This guarantees 100% reproducibility and complete auditability for enterprise sales leadership."*

---

### 4. "How do you prevent the Proposal Agent from promising features your company doesn't have?"
> *"We implement a closed-loop Grounding Validation pattern. The Solution Agent queries our ChromaDB vector catalog using dense embeddings (`all-MiniLM-L6-v2`) and passes only verified product capabilities into the proposal prompt context. 
> System prompts strictly forbid the Proposal Agent from inventing capabilities outside the retrieved catalog items. Finally, the independent Reviewer Agent cross-examines the generated proposal text against the verified catalog items to detect any ungrounded claims before human delivery."*

---

### 5. "How do you handle LLM rate limits and API quota exhaustion?"
> *"Our LLM service layer implements a circuit breaker with exponential backoff and jitter for transient 5xx errors or temporary token-per-minute rate limits. 
> However, if the provider returns a hard quota exhaustion error (such as a 429 indicating a depleted monthly credit), the service raises a specialized `ProviderQuotaError`. The orchestrator catches this immediately and fails fast, terminating downstream LLM calls rather than hanging the server in futile retry loops."*

---

### 6. "Why use FastAPI BackgroundTasks instead of processing synchronously?"
> *"A multi-agent workflow takes between 10 to 25 seconds because it coordinates multiple LLM calls, web searches, and vector retrieval. Holding an HTTP connection open for that duration blocks server worker threads, risks proxy/gateway timeouts (like Vercel's 30-second serverless execution limits), and degrades user experience. 
> By responding immediately with HTTP 202 Accepted and a `lead_id`, the client UI can display an interactive progress stepper that polls or streams status updates in real time."*

---

### 7. "How do you ensure database sessions don't leak in high-concurrency environments?"
> *"We use FastAPI's dependency injection system with a Python generator pattern:
> ```python
> def get_db():
>     db = SessionLocal()
>     try:
>         yield db
>     finally:
>         db.close()
> ```
> This ensures that even if an unhandled exception occurs mid-request, the database connection is guaranteed to be returned to the connection pool. For background tasks running outside the request scope, we instantiate dedicated `SessionLocal()` contexts with explicit try/finally closures."*

---

### 8. "How does your system qualify a 10,000 documents/month customer requirement?"
> *"When a requirement mentions 10,000 PDF documents per month, the Requirements Agent extracts the operational scale. The Scoring Engine evaluates this high enterprise volume, awarding the maximum +40 points under Opportunity Scale. 
> Simultaneously, the RAG service matches the document extraction requirement against our 'DocumentAI Pro' catalog item. Assuming the client has budget and timeline clarity, the lead scores $\ge 90/100$, automatically qualifying the opportunity."*

---

### 9. "What causes a lead to be flagged as 'Low Priority'?"
> *"A lead receives 'Low Priority' when its composite score falls below 50.0. This happens when:
> - The inquiry is identified as non-commercial, academic, or consumer-oriented (e.g., student homework, recipes), which drops the Fit Score to 15.
> - The budget is zero or missing, dropping Readiness to 10.
> - The organization is a single user with negligible volume, dropping Opportunity to 10.
> - High commercial unviability risk (85/100) penalizes the final calculation.
> The resulting score of ~12.25/100 deterministically routes the inquiry to Low Priority."*

---

### 10. "If you had to scale this system to 1,000 concurrent leads per minute, what would you change?"
> *"I would introduce three key architectural upgrades:
> 1. **Distributed Task Queue**: Replace in-process `BackgroundTasks` with Celery or Temporal backed by Redis/RabbitMQ to distribute agent workloads across horizontally auto-scaled worker nodes.
> 2. **Distributed Vector Database**: Migrate local ChromaDB to a managed, distributed vector store like Pinecone, Weaviate, or Qdrant with read replicas.
> 3. **Semantic Caching & Token Pooling**: Implement Redis-backed semantic caching (GPTCache) for similar company research queries and establish a multi-key LLM token pool to distribute API rate limits across enterprise accounts."*

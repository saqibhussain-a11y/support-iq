# SupportIQ — AI Customer Support Intelligence Platform

An AI-powered customer support platform that understands customer queries, retrieves relevant
company knowledge using RAG, generates grounded responses, validates them, decides whether to
resolve or escalate the issue, and evaluates the quality of the AI response.

This repository is being built module by module, following an AI Engineering roadmap from
foundational infrastructure through RAG, multi-agent orchestration, evaluation, and observability.

## Getting started

Only Postgres runs in Docker. The backend and frontend run natively on your machine — faster
iteration, no image rebuilds on every code change.

### 1. Start the database

```bash
cp .env.example .env
docker compose up -d
```

### 2. Start the backend

```bash
cd apps/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/health` → `{"status":"ok"}`

### 3. Start the frontend

```bash
cd apps/frontend
npm install
npm run dev
```

Visit http://localhost:3000.

## Module 1 — Foundation

This module set up the application skeleton only:

```text
Next.js (frontend)  →  FastAPI (backend)  →  PostgreSQL + pgvector
```

## Module 2 — LLM Layer

A provider-agnostic LLM abstraction, so agents (Module 5+) never call Groq directly:

```text
Agent  →  LLMService  →  ModelProvider (interface)  →  GroqProvider  →  Groq API
```

- `app/llm/provider.py` — `ModelProvider` abstract base class (`complete`, `stream`).
- `app/llm/groq_provider.py` — the only implementation today. Retries on transient errors are
  delegated to the official `groq` SDK's built-in `max_retries`, not hand-rolled.
- `app/llm/service.py` — `LLMService`, the ergonomic layer agents will actually call. Adds
  `complete_structured()`: request JSON-mode output from the model, then validate it against a
  Pydantic schema, raising `LLMError` if the model didn't comply.
- `app/llm/dependencies.py` — `get_llm_service()` wires `Settings` → `GroqProvider` → `LLMService`.

No agents, RAG, or LangGraph yet — this module is purely the LLM plumbing.

### Trying it live

Requires a real `GROQ_API_KEY` in `.env` (get one from console.groq.com):

```bash
cd apps/backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m scripts.demo_llm
```

This sends a sample "charged twice" support message through `LLMService.complete_structured()`
and prints the resulting `{category, priority, sentiment}` JSON.

## Module 3 — Knowledge Base & Indexing

Turns the markdown policy docs in `knowledge_base/` into embedded, searchable chunks in pgvector:

```text
knowledge_base/*.md  →  loader  →  chunker  →  EmbeddingProvider (fastembed, local)  →  document_chunks (pgvector)
```

- `knowledge_base/` — a small, controlled set of company policy docs (billing, refunds,
  subscriptions, accounts, support) with concrete, specific facts (a 30-day refund window, a
  5-7 business day processing time, etc.) so later evaluation modules have known expected answers.
- `app/knowledge/loader.py` — walks the directory tree; each doc's parent folder name becomes its
  `category` metadata.
- `app/knowledge/chunker.py` — splits each doc on `##` headings (one policy point per chunk), with
  a paragraph-boundary fallback if any section is unusually long.
- `app/embeddings/` — mirrors the `app/llm/` structure exactly: `EmbeddingProvider` (interface) →
  `FastEmbedProvider` (implementation). Embeddings run locally via `fastembed`
  (`BAAI/bge-small-en-v1.5`, 384 dimensions) — no API key, no per-call cost, since this is a
  capability the company controls and calls constantly (once per doc chunk, and later once per
  incoming query), unlike chat completions which benefit from a hosted model's reasoning quality.
- `app/db/models.py` + `alembic/` — the `document_chunks` table (pgvector column, HNSW index for
  cosine similarity) is created via an Alembic migration, not a one-shot init script. `db/init/`
  only runs once when the Postgres *volume* is first created; every later module will keep
  changing the schema, so migrations are the only approach that scales past Module 1.
- `app/knowledge/indexer.py` — orchestrates loader → chunker → embed → upsert. Re-running it is
  idempotent per document (existing chunks for a document are deleted and replaced).

No retrieval/search yet — that's Module 4. This module only gets the data in.

### Indexing the knowledge base

```bash
cd apps/backend
alembic upgrade head          # creates the document_chunks table
python -m scripts.index_knowledge_base
```

Prints a summary: documents processed, chunks created, chunks embedded, total rows now in the
table.

## Module 4 — RAG & Hybrid Retrieval

Turns a customer's question into the handful of policy chunks actually relevant to it:

```text
Query → embed → Dense search (pgvector cosine) + Sparse search (Postgres full-text)
      → RRF fusion → candidate set → Cross-encoder rerank → top-K chunks with scores
```

- **Why hybrid, not just dense?** Dense (embedding) search understands meaning ("charged twice"
  ≈ "duplicate charge") but can miss exact terms; sparse (keyword/full-text) search catches exact
  matches dense search sometimes ranks low. Running both and fusing catches what either alone
  would miss.
- `app/retrieval/dense.py` — pgvector cosine similarity via `.cosine_distance()`, using the same
  HNSW index built in Module 3.
- `app/retrieval/sparse.py` — Postgres full-text search (`to_tsvector`/`plainto_tsquery`/`ts_rank`)
  against a new generated `content_tsv` column (`alembic/versions/0002_...`) with a GIN index —
  a real schema change via migration, not a one-off script, for the same reason Module 3 used
  Alembic in the first place.
- `app/retrieval/fusion.py` — Reciprocal Rank Fusion (`score = Σ 1/(k + rank)` across each
  ranking a chunk appears in). Combines two differently-scaled rankings (cosine distance vs.
  `ts_rank`) without needing to normalize either — RRF only cares about rank position, not score
  magnitude, which is exactly why it's the standard way to merge rankings from unrelated scoring
  systems.
- `app/reranking/` — mirrors `app/llm/`/`app/embeddings/` exactly: `Reranker` (interface) →
  `FastEmbedReranker` (`Xenova/ms-marco-MiniLM-L-6-v2` cross-encoder, local, no API key). Dense
  and sparse search are fast but approximate at the top-20; a cross-encoder scores each
  (query, chunk) pair jointly and is far more accurate — but too slow to run over the whole table,
  so it only reorders the ~20 RRF-fused candidates, not all 39 rows.
- `app/retrieval/service.py` — `RetrievalService` orchestrates all of the above. Note: dense and
  sparse search run **sequentially** on the same `AsyncSession`, not concurrently via
  `asyncio.gather` — a single SQLAlchemy async session can't safely run two queries at once; this
  was an actual bug caught during live verification, not a hypothetical one.

No agents yet — `RetrievalService` is a building block Module 5's Response Agent will call, not
a user-facing feature itself.

### Querying the knowledge base

```bash
cd apps/backend
python -m scripts.query_knowledge_base "Can I get a refund for a duplicate subscription charge?"
```

Prints the top-K chunks ranked by rerank score, each with its fused (RRF) score, source document,
and category.

## Module 5 — Customer Support Agents

Two focused agents, each a thin, testable layer over the services built in Modules 2–4 — no
orchestration between them yet, that's Module 6 (LangGraph):

```text
ClassifierAgent:  ticket text  →  LLMService (structured JSON)  →  category/priority/sentiment
ResponseAgent:    question     →  RetrievalService  →  LLMService (grounded in retrieved chunks)  →  answer + sources
```

- `app/agents/classifier.py` — `ClassifierAgent` formalizes what Module 2's `demo_llm.py` did
  ad hoc: classifies an incoming message into `category` / `priority` / `sentiment` via
  `LLMService.complete_structured()`. The schema now uses `Literal` types
  (`app/agents/schemas.py`) instead of the demo's plain `str` fields, so an out-of-vocabulary
  value from the model fails validation loudly instead of silently passing through.
- `app/agents/response.py` — `ResponseAgent` is the "Response Agent" foreshadowed in Module 4: it
  calls `RetrievalService.search()` to get the top-K chunks, builds a context block from them, and
  asks the LLM to answer **using only that context**. The system prompt (`app/agents/prompts.py`)
  explicitly instructs the model to say it doesn't know rather than guess.
- **Sources are computed from retrieval results, not asked of the LLM.** The model never invents
  which documents it used — `sources` is just the deduplicated, sorted list of `document` values
  from the chunks that were actually retrieved. This removes an entire class of citation
  hallucination by construction.
- **Honest limitation, found via live verification, not assumed:** `SupportResponse.grounded` is
  `True` whenever retrieval returns *any* candidates — RRF + reranking always return the top-K by
  rank, with no relevance floor, even if none of them are actually relevant. Asking a real,
  out-of-scope question ("What is the capital of France?") returned `grounded=True` with sources
  from unrelated docs, yet the LLM still correctly refused to answer using irrelevant context,
  because that refusal is enforced by the prompt, not by the `grounded` flag. Real groundedness /
  hallucination detection (checking that the answer is actually *supported* by the context, not
  just that context existed) is Module 9's job — `grounded` here only means "retrieval ran and
  found candidates."
- `app/agents/dependencies.py` — `get_classifier_agent()` / `get_response_agent()`, same DI pattern
  as every other module.

### Trying the agents live

```bash
cd apps/backend
python -m scripts.demo_agents "I was charged twice for my subscription this month and I want a refund."
```

Prints the ticket classification, then the grounded response with its sources.

## Module 6 — LangGraph Orchestration

Module 5's two agents had to be called manually, in order, by whatever script wanted them
(`demo_agents.py` just calls `classify()` then `respond()` back to back). Module 6 replaces that
manual sequencing with an actual graph: explicit state, explicit nodes, and an explicit
conditional edge that decides which path a ticket takes.

```text
START → classify ──► category == "other" ──► clarify ──► END
                └──► anything else ──────────► respond ──► END
```

- `app/workflows/schemas.py` — `TicketState` (a `TypedDict`: `message`, `classification`,
  `response`) is the state LangGraph threads through the graph; each node returns only the keys
  it changed, and LangGraph merges them in. `WorkflowContext` is a small dataclass
  (`classifier`, `responder`, `session`) injected into nodes at invoke time via LangGraph's
  `Runtime[Context]` — dependency injection for graph nodes, so nodes stay pure functions of
  `(state, runtime)` instead of closing over module-level singletons.
- `app/workflows/nodes.py` — `classify_node` and `respond_node` just call the Module 5 agents;
  `clarify_node` returns a canned "please give me more detail" response without touching
  retrieval or the LLM at all. `route_after_classification` is the conditional: `category ==
  "other"` → `clarify`, otherwise → `respond`.
- `app/workflows/graph.py` — `build_support_workflow()` builds and compiles the `StateGraph` once
  (cached — the graph's structure is static; only the per-request `WorkflowContext` varies).
- `app/workflows/service.py` — `SupportWorkflowService.run()` is the one call site: builds a
  `WorkflowContext`, seeds the initial state, and `ainvoke()`s the compiled graph.
- `app/api/tickets.py` — the first real feature endpoint: `POST /api/tickets` takes
  `{"message": "..."}` and runs it through the graph, returning both the classification and the
  grounded response. Added `get_db_session` to `app/db/session.py` as a FastAPI-`Depends`-shaped
  wrapper around the existing `session_scope()`.
- **Verified live, not assumed:** running the vague message `"hey"` through the real graph
  produced the `clarify` answer in ~3.4s total container time — with none of fastembed's or the
  reranker's ONNX model downloads/loads happening at all. That confirms the conditional edge
  genuinely short-circuits the expensive retrieval+rerank+LLM path for the `clarify` branch,
  rather than running it anyway and discarding the result.

Still no validation, quality checks, or human-escalation policy — the routing rule here
(`category == "other"`) exists only to demonstrate the conditional edge. Real escalation logic is
Module 7.

### Trying the workflow live

```bash
cd apps/backend
python -m scripts.demo_workflow "I was charged twice for my subscription this month and I want a refund."
```

Or through the API once the backend is running:

```bash
curl -s http://localhost:8000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"message": "I was charged twice for my subscription this month and I want a refund."}'
```

## Module 7 — Validation & Escalation (current)

A deterministic rule layer sits between the LLM's answer and the customer, deciding whether a
human needs to see this ticket before (or instead of) the automated response going out. This is
plain Python `if`/`in` logic, not another LLM call — the point is an auditable, unit-testable
safety net over LLM output, not a second opinion from the same kind of model that could fail the
same way.

```text
respond/clarify → validate (deterministic rules) → escalation: none | review | immediate
```

- `app/validation/rules.py` — `evaluate()`, built directly from the three tiers documented in
  `knowledge_base/support/escalation_policy.md`:
  - **immediate** — the raw customer message contains fraud/unauthorized-access/stolen-payment
    language. Checked against the *message itself*, not the LLM's `category` classification — so
    a misclassified ticket (e.g. the classifier calls it `"other"`) still gets caught. Verified
    live: this exact case happened during testing, and the keyword check caught it anyway.
  - **review** — a high-priority billing dispute where retrieval's confidence was low, using
    `SupportResponse.top_rerank_score` (see below) rather than the old boolean `grounded` flag.
  - **none** — everything else resolves automatically.
- `app/agents/schemas.py` / `app/agents/response.py` — added `SupportResponse.top_rerank_score`
  (the best cross-encoder score among the retrieved chunks). This replaces `grounded` as the
  input to confidence-based rules: `grounded` only means "retrieval returned candidates,"
  regardless of relevance (the exact gap flagged in Modules 5–6); `top_rerank_score` is a real
  number that empirically separates the cases. Verified against real retrieval output before
  picking a threshold: a genuinely relevant top match scored 5.9 and 2.6 on two real queries, an
  irrelevant one ("What is the capital of France?") scored **-11.2** — a threshold of `0.0` cleanly
  separates them on real data, not a guessed constant.
- `app/workflows/nodes.py` — new `validate_node`, wired in after both `respond` and `clarify`
  (`app/workflows/graph.py`), so every path through the graph gets checked, including the
  cheap `clarify` path.

**Real limitation, found live, not patched over:** running the exact "renewal refund I forgot to
cancel in time" example from `escalation_policy.md` — which the doc itself calls out as needing
human judgment — returned `escalation: none`. Retrieval was confident (`top_rerank_score` 2.64,
genuinely the right documents), so the low-confidence rule correctly didn't fire; but "confident,
well-grounded retrieval" and "this is a case-by-case judgment call" are different problems, and
this rule layer only detects the first one. I'm not patching this with a rule fitted to one
example — that would just be overfitting to a single sentence, not a real fix. Actually
distinguishing "the docs answer this clearly" from "this requires case-by-case judgment" needs
either a real quality signal (Module 8, Evaluation) or a self-critique step (Module 9,
hallucination detection), not more keyword lists.

### Trying it live

```bash
cd apps/backend
python -m scripts.demo_workflow "I think someone stole my card"
```

Prints classification, response, and now escalation level + reasons.

### Stack

| Layer      | Technology                              |
| ---------- | ---------------------------------------- |
| Frontend   | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, shadcn/ui |
| Backend    | FastAPI, Pydantic v2, SQLAlchemy (async), Alembic, Groq SDK, fastembed, LangGraph |
| Database   | PostgreSQL 16 + pgvector                 |
| Infra      | Docker Compose (Postgres only) — backend and frontend run natively |

### Project structure

```text
supportiq/
├── apps/
│   ├── frontend/        # Next.js app
│   └── backend/         # FastAPI app
│       ├── app/
│       │   ├── api/     # Route handlers (health checks for now)
│       │   ├── core/    # Settings/config
│       │   ├── db/      # Database engine/session/ORM models
│       │   ├── llm/     # ModelProvider / GroqProvider / LLMService
│       │   ├── embeddings/  # EmbeddingProvider / FastEmbedProvider
│       │   ├── knowledge/   # loader / chunker / indexer for knowledge_base/
│       │   ├── retrieval/   # dense + sparse search, RRF fusion, RetrievalService
│       │   ├── reranking/   # Reranker / FastEmbedReranker
│       │   ├── agents/      # ClassifierAgent / ResponseAgent
│       │   ├── workflows/   # LangGraph StateGraph wiring the agents together
│       │   ├── validation/  # Deterministic escalation rules
│       │   └── main.py
│       ├── alembic/     # Schema migrations
│       ├── scripts/     # Manual demo/verification/indexing scripts
│       └── tests/
├── packages/            # Code shared between apps (empty for now)
├── knowledge_base/      # Company policy docs (billing, refunds, subscriptions, accounts, support)
├── db/init/             # Enables the pgvector extension once, on first Postgres container start
├── docker-compose.yml
└── .env.example
```

## Testing

```bash
# Backend
cd apps/backend && pip install -r requirements-dev.txt && pytest

# Frontend
cd apps/frontend && npm test
```

## Roadmap

Later modules add: the LLM abstraction layer (Groq), the knowledge base + embeddings pipeline,
hybrid RAG retrieval, the multi-agent support workflow, LangGraph orchestration, validation and
escalation rules, evaluation and hallucination detection, and observability (LangSmith, Helicone,
OpenTelemetry). See project instructions for the full module breakdown.

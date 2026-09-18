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

## Module 3 — Knowledge Base & Indexing (current)

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

### Stack

| Layer      | Technology                              |
| ---------- | ---------------------------------------- |
| Frontend   | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, shadcn/ui |
| Backend    | FastAPI, Pydantic v2, SQLAlchemy (async), Alembic, Groq SDK, fastembed |
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

# SupportIQ — AI Customer Support Intelligence Platform

An AI-powered customer support platform that understands customer queries, retrieves relevant
company knowledge using RAG, generates grounded responses, validates them, decides whether to
resolve or escalate the issue, and evaluates the quality of the AI response.

This repository is being built module by module, following an AI Engineering roadmap from
foundational infrastructure through RAG, multi-agent orchestration, evaluation, and observability.

## Module 1 — Foundation (current)

This module sets up the application skeleton only:

```text
Next.js (frontend)  →  FastAPI (backend)  →  PostgreSQL + pgvector
```

No AI/RAG/agent functionality is implemented yet — that begins in Module 2.

### Stack

| Layer      | Technology                              |
| ---------- | ---------------------------------------- |
| Frontend   | Next.js 16 (App Router), TypeScript, Tailwind CSS v4, shadcn/ui |
| Backend    | FastAPI, Pydantic v2, SQLAlchemy (async) |
| Database   | PostgreSQL 16 + pgvector                 |
| Infra      | Docker, Docker Compose                   |

### Project structure

```text
supportiq/
├── apps/
│   ├── frontend/        # Next.js app
│   └── backend/         # FastAPI app
│       ├── app/
│       │   ├── api/     # Route handlers (health checks for now)
│       │   ├── core/    # Settings/config
│       │   ├── db/      # Database engine/session
│       │   └── main.py
│       └── tests/
├── packages/            # Code shared between apps (empty for now)
├── db/init/             # SQL run once when the Postgres container first initializes
├── docker-compose.yml
└── .env.example
```

## Running with Docker Compose (recommended)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Backend health check: http://localhost:8000/health
- Backend readiness (checks DB connectivity): http://localhost:8000/health/ready

## Running services individually (local dev without Docker)

### Backend

```bash
cd apps/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The backend reads `DATABASE_URL` from the environment (see `.env.example`). When running outside
Docker, point it at `localhost` instead of the `postgres` service hostname.

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` (see `.env.example`) if the backend isn't running on the default
`http://localhost:8000`.

### Database only

If you just want Postgres+pgvector running locally while developing the backend directly:

```bash
docker compose up postgres
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

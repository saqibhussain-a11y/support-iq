.PHONY: db-up db-down db-logs test-backend test-frontend migrate index-knowledge-base

db-up:
	docker compose up -d

db-down:
	docker compose down

db-logs:
	docker compose logs -f

test-backend:
	cd apps/backend && pip install -r requirements-dev.txt -q && pytest

test-frontend:
	cd apps/frontend && npm test

migrate:
	cd apps/backend && alembic upgrade head

index-knowledge-base:
	cd apps/backend && python -m scripts.index_knowledge_base

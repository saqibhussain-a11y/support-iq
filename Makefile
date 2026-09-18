.PHONY: up down logs test-backend test-frontend

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test-backend:
	cd apps/backend && pip install -r requirements-dev.txt -q && pytest

test-frontend:
	cd apps/frontend && npm test

COMPOSE = docker compose --env-file .env -f infra/docker/compose.yaml

.PHONY: env up up-mail down sync api worker test lint web

env:
	@test -f .env || cp .env.example .env

up: env
	$(COMPOSE) up -d --wait

up-mail: env
	$(COMPOSE) --profile dev-mail up -d --wait

down:
	$(COMPOSE) --profile dev-mail down

sync:
	uv sync

api: env sync
	set -a && . ./.env && set +a && uv run aih-api

worker: env sync
	set -a && . ./.env && set +a && uv run aih-worker

test: sync
	uv run pytest

lint: sync
	uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports

web:
	npm run dev --workspace @aka/admin-web

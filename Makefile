COMPOSE = docker compose --env-file .env -f infra/docker/compose.yaml

.PHONY: env up up-mail down api worker test web

env:
	@test -f .env || cp .env.example .env

up: env
	$(COMPOSE) up -d --wait

up-mail: env
	$(COMPOSE) --profile dev-mail up -d --wait

down:
	$(COMPOSE) --profile dev-mail down

api: env
	set -a && . ./.env && set +a && mvn -pl apps/api -am spring-boot:run

worker: env
	set -a && . ./.env && set +a && mvn -pl apps/worker -am spring-boot:run

test:
	mvn -B verify

web:
	npm run dev --workspace @aka/admin-web

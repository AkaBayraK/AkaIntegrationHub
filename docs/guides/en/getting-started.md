# Getting started (local development)

1. Copy `.env.example` to `.env` (`make up` does it automatically) and change the passwords.
2. `make up` — waits until PostgreSQL 17.6, Valkey 8.1.4 and RabbitMQ 4.1.4 are healthy.
3. `make api` — on first start the API creates the `platform` schema through Flyway.
4. Readiness check: `curl localhost:28081/actuator/health/readiness` → `{"status":"UP"}`.
   Readiness is `UP` only when the database, Valkey and RabbitMQ are all reachable.
5. `curl -H 'X-Correlation-Id: trial-0001' localhost:28080/v1/system/info` — the same correlation id is echoed back.
6. Admin console: `npm install && npm run build && make web` → http://localhost:28030. In the development shell
   "Sign in" does not authenticate yet (PHASE-02).

## Troubleshooting
- **Port in use:** change the `AIH_*_HOST_PORT` values in `.env` and pass the same values to the apps via
  `AIH_DB_URL`, `AIH_VALKEY_PORT`, `AIH_RABBITMQ_PORT`.
- **Tests cannot find Docker:** Testcontainers needs a running Docker daemon.

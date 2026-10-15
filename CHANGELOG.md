# Changelog

## [Unreleased]
### PHASE-01 — Foundation & Branding
- Maven reactor: `aih-common`, `aih-api`, `aih-worker` (Spring Boot 4.1.1, Java 21 bytecode).
- API: liveness/readiness (PostgreSQL + Valkey + RabbitMQ), ayrı yönetim portu, `X-Correlation-Id`, RFC 9457 hata modeli, `GET /v1/system/info`, Flyway ilk migration.
- Worker: RabbitMQ bağlantısı ve readiness.
- Docker Compose: PostgreSQL 17.6, Valkey 8.1.4, RabbitMQ 4.1.4, Mailpit (`dev-mail` profili); yalnız `127.0.0.1`.
- `@aka/design-tokens`, `@aka/integration-ui` (provider/adapters, AppShell, LoginShell, TR/EN, light/dark), Next.js 16 admin kabuğu.
- Özgün logo SVG varyantları, favicon, marka kılavuzu.
- GitHub Actions CI: backend testleri, web build/typecheck/test, CycloneDX SBOM, Markdown link kontrolü.

### PHASE-00 — Discovery & License Gate
- ADR-0001…0012, lisans envanteri, bağımlılık politikası, tehdit modeli, risk raporu.

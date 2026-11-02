# Changelog

## [Unreleased]
### PHASE-01R — Backend Python/FastAPI geçişi
- `aih-api`, `aih-worker`, `aih-common` Python 3.13 / FastAPI ile yeniden yazıldı (uv workspace); Java/Maven kaynakları kaldırıldı.
- Aynı davranış: `GET /v1/system/info`, `X-Correlation-Id`, RFC 9457 hata modeli (`AIH-COMMON-xxx`), ayrı yönetim portunda
  `/actuator/health/{liveness,readiness}` (PostgreSQL + Valkey + RabbitMQ), ortam değişkenleri ve portlar değişmedi.
- Flyway yerine Alembic; ilk revizyon Flyway ile kurulmuş veritabanlarında da güvenle çalışır.
- JSON log + sır/kimlik bilgisi alan maskeleme (structlog).
- Testler: pytest + Testcontainers (23 test); CI: ruff, mypy --strict, import-linter, Python CycloneDX SBOM.

### Mimari karar önerileri (kod değişikliği yok)
- ADR-0013: backend'in Python/FastAPI'ye taşınması önerisi; PHASE-01R planı (`docs/plans/PYTHON_MIGRATION_PLAN.md`).
- ADR-0014: MCP tabanlı AI yapılandırma asistanı; PHASES.md'ye PHASE-01R ve PHASE-17 eklendi.

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

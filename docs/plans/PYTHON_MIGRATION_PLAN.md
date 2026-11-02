# PHASE-01R — Backend'in Python'a taşınma planı

**Durum:** Uygulandı (PHASE-01R, issue #33) · **İlgili:** ADR-0013, ADR-0014

## Amaç
PHASE-01'in backend kabul kriterlerini Python/FastAPI ile aynen sağlamak. Frontend, altyapı ve iş kuralları değişmez.

## Mevcut Java iskeleti → Python karşılığı

| Mevcut (Java) | Python karşılığı | Kabul |
|---|---|---|
| `AkaIntegrationHubApiApplication` | `aih_api.main:app` (FastAPI, Uvicorn) | `make api` ile ayağa kalkar |
| `SystemInfoController` `GET /v1/system/info` | Aynı yol ve aynı JSON şeması | Admin web değişmeden çalışır |
| `CorrelationIdFilter` + `CorrelationIds` | ASGI middleware + `contextvars` | Header üretimi/taşınması ve doğrulama testleri |
| `GlobalExceptionHandler` + `ApiErrorCode` | Exception handler'lar, `application/problem+json`, aynı `AIH-COMMON-xxx` kodları | Stacktrace ve iç mesaj sızmaz |
| `PlatformProperties`, `application.yml` | pydantic-settings; aynı `AIH_*` değişkenleri ve portlar | `.env.example` aynı kalır |
| Actuator liveness/readiness (db, redis, rabbit) | Ayrı yönetim portunda aynı yollar: `/actuator/health/liveness`, `/actuator/health/readiness` | Bağımlılık düşünce readiness `DOWN` (503) |
| Flyway `V202610151200__create_platform_schema.sql` | Alembic ilk revizyonu (aynı SQL) | Mevcut veritabanında tekrar çalışmaz, şema aynı |
| `aih-worker` (RabbitMQ health) | `aih_worker` (aio-pika bağlantısı + health) | Readiness RabbitMQ'ya bağlı |
| JUnit + Testcontainers (15 test) | pytest + testcontainers-python | Eşdeğer senaryolar yeşil |
| ECS structured log | structlog JSON + maskeleme | Sır alanları loglanmaz |

## Adımlar
1. `pyproject.toml` uv workspace, `ruff`, `mypy --strict`, `import-linter` kontratları.
2. `modules/common` (correlation, hata modeli, ayarlar, logging) ve birim testleri.
3. `apps/api`: system info, health, problem details; Testcontainers entegrasyon testleri.
4. Alembic: mevcut Flyway SQL'ini ilk revizyon olarak taşı; Flyway geçmiş tablosu olan ortamlarda `alembic stamp` notu.
5. `apps/worker`: RabbitMQ bağlantısı ve health.
6. `Makefile` (`api`, `worker`, `test`), CI backend işi (Python kurulum, uv, test, CycloneDX Python SBOM), lisans envanteri.
7. Dokümanlar: getting-started TR/EN, ADR-0002/0004 işaretleri, `docs/phases/PHASE_STATUS.md`.
8. Java kaynakları aynı PR'da kaldırıldı: Python eşdeğer testleri (23) yeşil olduğu için iki yığını paralel tutmanın faydası yoktu.

## Açık sorular
- Python 3.13 mü 3.14 mü? (Öneri: 3.13; 3.14 CI matrisinde)
- PHASE-01'in mevcut "Onay bekliyor" durumu: Java iskeleti onaylanmadan doğrudan PHASE-01R'ye geçilmesi önerilir.

## Riskler
- Admin web'in API sözleşmesine bağımlılığı: OpenAPI diff kontrolü CI'a eklenmeli.
- Ekip Java deneyimi: Spring'deki hazır güvenlik varsayılanları Python'da elle kurulmalı; PHASE-02 güvenlik testleri kritik.

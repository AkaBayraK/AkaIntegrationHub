# ADR-0013 — Backend dili: Python (FastAPI)

**Durum:** Önerildi · **Faz:** PHASE-01R (PHASE-01 backend yeniden yazımı) · **Değiştirdiği:** ADR-0002'nin backend satırları, ADR-0001'in Maven modül detayları, ADR-0004'ün migration aracı

## Bağlam
PHASE-01'de backend Java 21 / Spring Boot 4.1.1 ile iskelet olarak kuruldu (`apps/api`, `apps/worker`, `modules/common`).
İş mantığı henüz yok: yalnızca health/readiness, `/v1/system/info`, correlation id filtresi, problem-details hata modeli
ve tek bir platform migration'ı var. Ürün sahibi backend'i Python ile geliştirmek ve yapay zekâ / MCP entegrasyonunu
(ADR-0014) birinci sınıf yapmak istiyor. Yeniden yazımın maliyeti şu an projenin ömrü boyunca en düşük seviyesinde.

## Karar
- Backend dili **Python**, web framework'ü **FastAPI**. API ve worker aynı Python kod tabanından iki ayrı süreç olarak çalışır
  (ADR-0001'deki modüler monolit + ayrı worker ilkesi korunur).
- Frontend (`apps/admin-web`, `packages/ui-react`, `packages/design-tokens`), Docker Compose altyapısı (PostgreSQL, Valkey,
  RabbitMQ, Mailpit), ADR-0003 sorumluluk matrisi ve tüm iş kuralları **değişmez**.
- Java/.NET/TypeScript SDK stratejisi (ADR-0010) **değişmez**: SDK'lar istemci kütüphaneleridir ve OpenAPI 3.1 sözleşmesinden
  üretilir; backend dilinden bağımsızdır. Java SDK'nın Java 21 baseline'ı korunur.

## Önerilen Python yığını
Sürümler PHASE-01R'de resmi kaynaklardan (PyPI, python.org) okunup pinlenir; aşağıdaki lisanslar da o sırada yeniden doğrulanır.

| İhtiyaç | Seçim | Lisans (SPDX, doğrulanacak) | Not |
|---|---|---|---|
| Dil | CPython 3.13 | PSF-2.0 | 3.14 uyumluluğu PHASE-01R'de test edilir |
| Paket/ortam yönetimi | uv + `pyproject.toml` workspace | MIT / Apache-2.0 | Kilit dosyası (`uv.lock`) commit edilir |
| Web / OpenAPI 3.1 | FastAPI + Pydantic v2 + Uvicorn | MIT / MIT / BSD-3-Clause | OpenAPI 3.1 yerleşik üretilir |
| ORM | SQLAlchemy 2.x (async) | MIT | |
| PostgreSQL sürücüsü | asyncpg | Apache-2.0 | psycopg 3 LGPL-3.0 olduğu için varsayılan değil |
| Migration | Alembic | MIT | Flyway'in yerini alır (ADR-0004 değişir) |
| Valkey istemcisi | redis-py (`redis.asyncio`) | MIT | Valkey protokol uyumu PHASE-15'te test edilir |
| RabbitMQ istemcisi | aio-pika | Apache-2.0 | Outbox, retry, DLQ kontrolü uygulamada kalır; Celery kullanılmaz |
| Ayarlar | pydantic-settings | MIT | Mevcut `AIH_*` ortam değişkenleri korunur |
| JWT / OIDC | PyJWT (+ cryptography) | MIT / Apache-2.0 veya BSD | PHASE-02 |
| Loglama | structlog (JSON) | MIT veya Apache-2.0 | Sır/PII maskeleme processor'ı zorunlu |
| Telemetri | OpenTelemetry Python SDK + instrumentation | Apache-2.0 | ADR-0012 değişmez |
| MCP | Resmi MCP Python SDK (`mcp`) | MIT | ADR-0014 |
| Test | pytest, pytest-asyncio, httpx, testcontainers-python | MIT / Apache-2.0 / BSD-3-Clause / Apache-2.0 | |
| Kalite | ruff, mypy (strict), import-linter | MIT / MIT / BSD-2-Clause | import-linter ArchUnit'in yerini alır |

## Hedef dizin yapısı
```
apps/api/            # FastAPI uygulaması (aih_api)
apps/worker/         # RabbitMQ tüketicisi (aih_worker)
apps/mcp/            # MCP sunucusu (aih_mcp) — PHASE-17, ADR-0014
modules/common/      # aih_common: correlation id, hata modeli, ayarlar, logging
modules/<domain>/    # identity, tenancy, providers, notifications, ... (her biri ayrı Python paketi)
migrations/          # Alembic
pyproject.toml       # uv workspace
```
Modül sınırları: her domain paketinde `api` (dışa açık) ve `internal` alt paketleri olur; başka modülün `internal`
paketine import yasağı **import-linter** kontratlarıyla CI'da zorlanır. Her modül kendi PostgreSQL şemasının sahibidir.

## Sonuçlar
- **Olumlu:** MCP ve LLM ekosistemine doğrudan erişim, tek dilde AI + iş mantığı, FastAPI ile yerleşik OpenAPI 3.1,
  daha kısa kod. Mevcut frontend ve altyapı aynen kalır.
- **Olumsuz / riskler:**
  - Python dinamik tipli: `mypy --strict` ve Pydantic şemaları CI kapısı olmalı.
  - GIL nedeniyle CPU-yoğun iş tek süreçte ölçeklenmez; AIH I/O ağırlıklı olduğu için async + birden çok worker süreci yeterli.
  - Spring Security, Spring Data, Actuator gibi hazır bileşenlerin karşılıkları elle birleştirilecek (auth, health, problem details).
  - PHASE-01 Java testleri (15 Maven testi) pytest eşdeğerleriyle yeniden yazılmalı; kabul kriterleri aynı kalır.
  - Java/.NET müşterileri için davranış SDK'lar üzerinden aynıdır; sözleşme testleri (OpenAPI diff) önemi artar.
- Java kaynakları, Python eşdeğer testleri yeşil olduğu PHASE-01R PR'ında kaldırılır.

## Alternatifler
- **Spring Boot'ta kalmak:** çalışan iskelet ve dokümanlarla tam uyum; MCP Spring AI ile de yazılabilir. Ürün sahibi
  Python tercihi nedeniyle reddedildi.
- **Karma (Java çekirdek + Python AI servisi):** iki dil, iki CI hattı ve iki dağıtım birimi; self-hosted operasyon
  yükünü artırdığı için reddedildi.
- **Django:** yerleşik admin ve ORM güçlü, fakat admin UI zaten Next.js'te; async ve OpenAPI 3.1 için FastAPI daha uygun.
- **Celery:** yaygın, fakat retry/DLQ/idempotency kurallarını (PHASE-06) kendi semantiğine bağlar; aio-pika ile açık kontrol tercih edildi.

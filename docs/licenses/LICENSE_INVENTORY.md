# Lisans Envanteri (ilk sürüm)

> Hukuki görüş değildir. "Doğrulandı" = resmi registry/POM/repo beyanı okundu; transitive bağımlılık taraması
> CI'daki SBOM adımıyla (PHASE-01) yapılır. Durum: **DOĞRULANMADI** olanlar kullanılmadan önce tekrar kontrol edilir.

## Çalışma zamanı servisleri (container image)

| Bileşen | Sürüm | SPDX | Dağıtım modeli | Yükümlülük / Not | Durum |
|---|---|---|---|---|---|
| PostgreSQL | 17.6 | PostgreSQL | Ayrı servis | Telif bildirimi | Doğrulandı |
| Valkey | 8.1.4 | BSD-3-Clause | Ayrı servis | Telif bildirimi | Doğrulandı |
| RabbitMQ | 4.1.4 | MPL-2.0 | Ayrı servis, değiştirilmemiş | Image yeniden dağıtılırsa kaynak bağlantısı | Doğrulandı, hukuk teyidi önerilir |
| Mailpit | v1.27.10 | MIT | Yalnızca dev/test profili | Üründe dağıtılmaz | Doğrulandı |
| Keycloak | 26.4.1 | Apache-2.0 | Opsiyonel IdP | NOTICE | Doğrulandı |
| Prometheus, Alertmanager, Blackbox Exporter | PHASE-10'da pinlenir | Apache-2.0 | Opsiyonel profil | NOTICE | DOĞRULANMADI (sürüm) |
| OpenTelemetry Collector Contrib | PHASE-10'da pinlenir | Apache-2.0 | Opsiyonel profil | NOTICE | DOĞRULANMADI (sürüm) |
| Grafana, Loki, Tempo | PHASE-10'da pinlenir | **AGPL-3.0** | Opsiyonel profil | SaaS/dağıtım için **hukuk onayı şart** | Engelli (onay bekliyor) |

## Uygulama bağımlılıkları (doğrudan)

| Bileşen | Sürüm | SPDX | Kapsam | Durum |
|---|---|---|---|---|
| CPython | 3.13 | PSF-2.0 | runtime | Doğrulandı |
| FastAPI | 0.162.0 | MIT | runtime | Doğrulandı (PyPI, 2026-11-02) |
| Starlette (FastAPI üzerinden) | uv.lock | BSD-3-Clause | runtime | Doğrulandı |
| Uvicorn | 0.54.0 | BSD-3-Clause | runtime | Doğrulandı |
| Pydantic / pydantic-settings | 2.14.2 / 2.16.2 | MIT | runtime | Doğrulandı |
| SQLAlchemy | 2.1.6 | MIT | runtime | Doğrulandı |
| asyncpg | 0.32.0 | Apache-2.0 | runtime | Doğrulandı |
| Alembic | 1.20.1 | MIT | runtime | Doğrulandı |
| redis-py | 8.1.0 | MIT | runtime | Doğrulandı |
| aio-pika | 10.2.2 | Apache-2.0 | runtime | Doğrulandı |
| structlog | 26.1.0 | MIT OR Apache-2.0 | runtime | Doğrulandı |
| pytest / pytest-asyncio | 9.2.0 / 1.4.1.post1 | MIT / Apache-2.0 | test (dağıtılmaz) | Doğrulandı |
| httpx | 0.28.1 | BSD-3-Clause | test | Doğrulandı |
| testcontainers-python | 4.15.0 | Apache-2.0 | test | Doğrulandı |
| ruff / mypy / import-linter | 0.17.3 / 2.4.1 / 2.15 | MIT / MIT / BSD-2-Clause | build | Doğrulandı |
| cyclonedx-bom (Python) | 7.6.0 | Apache-2.0 | build | Doğrulandı |
| Next.js | 16.4.1 | MIT | runtime (web) | Doğrulandı |
| React | 19.x | MIT | runtime (web) | Doğrulandı |
| Tailwind CSS | 4.x | MIT | build | Eklenmedi (PHASE-08) |
| TypeScript | 5.9.3 | Apache-2.0 | build | Doğrulandı |
| Testing Library (react, jest-dom), jsdom | 16.3.3 / 7.0.1 / 30.1.3 | MIT | test | Doğrulandı |
| Vitest | 5.x | MIT | test | Doğrulandı |
| Docusaurus | 3.x | MIT | docs (PHASE-16) | Doğrulandı |

## İlk SBOM taraması (2026-10-15, PHASE-01)

- **Maven (126 bileşen):** 103 Apache-2.0, 8 BSD-3-Clause, 5 MIT, diğerleri çift lisanslı ve izin verici seçenekli:
  logback (EPL-2.0 / LGPL-2.1), jakarta.* (EPL-2.0 / GPL-2.0-CPE / BSD-3), aspectjweaver (EPL-2.0),
  amqp-client (Apache-2.0 / MPL-2.0 / GPL-2.0 — Apache-2.0 seçilir). Engelli lisans yok.
- **npm prod (18 bileşen):** MIT/Apache-2.0/ISC/0BSD dışında inceleme gerektirenler:
  - `@img/sharp-libvips-*` **LGPL-3.0-or-later** — Next.js görsel optimizasyonunun opsiyonel native bağımlılığı,
    dinamik bağlı. Self-hosted dağıtımda LGPL bildirimi gerekir; alternatif `images.unoptimized`. Karar PHASE-08.
  - `caniuse-lite` **CC-BY-4.0** — veri dosyası; atıf NOTICE'a eklenir.
  - `UNKNOWN` görünen 3 paket AIH'nin kendi workspace paketleridir (`UNLICENSED`).

## Reddedilen / engelli

| Bileşen | Sebep |
|---|---|
| Liquibase 5.x | FSL-1.1-ALv2 (rakip kullanım kısıtı) |
| Redis ≥ 7.4 | RSALv2/SSPLv1 (8.x'te AGPLv3 seçeneği) — onaysız kullanılmaz |
| Grafana/Loki/Tempo | AGPL-3.0 — hukuk onayına kadar yalnızca opsiyonel dev profili planlanır |

## Marka varlıkları
- `BRAND_CONCEPT.png` yalnızca referanstır; PHASE-01'deki SVG logo özgün olarak elle çizilir. Font olarak sistem
  font yığını kullanılır (ek font lisansı yok). Marka adı/alan adı tescil araştırması **yapılmadı** (risk R-01).

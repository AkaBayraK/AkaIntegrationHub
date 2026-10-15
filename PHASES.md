# AKA INTEGRATION HUB — PHASES

> Her faz için analiz → ADR → kontrat → uygulama → test → demo → onay. Tek faz/çalıştırma.

## PHASE-00 — Discovery & License Gate
Mevcut repoların entegrasyon gereksinimleri, deployment ve ürün stratejisi; SaaS/self-hosted matris; teknoloji ve transitive dependency lisans analizi; threat model; maliyet modeli. Kabul: onaylı kapsam, ADR, ilk SBOM/policy, risk listesi. Kod değişikliği yok.

## PHASE-01 — Foundation & Branding
Repo, CI/CD, local Docker (PostgreSQL, Valkey, RabbitMQ), backend/web skeleton, health/readiness, migration altyapısı; Aka Integration Hub marka kılavuzu, özgün A-akış logo SVG, favicon, monochrome/dark/light ikonlar, design tokens, TR/EN. Kabul: tek komutla lokal start, sağlık testleri, temel login shell, marka varlıkları.

## PHASE-02 — Identity, Tenant & Project
PlatformAdmin, TenantAdmin, ProjectAdmin, Operator, Viewer, ServiceAccount; tenant/project, OIDC/Keycloak, API key, RBAC, project scopes, invitation, tenant isolation, audit. Kabul: cross-tenant negatif testler, anahtar rotasyonu.

## PHASE-03 — Provider Registry & Adapter SDK
Provider türleri/capabilities, credentials secret refs, account configuration, adapter SPI, connection tests, enable/disable, priorities, health, sandbox. SMTP tenant/proje bazlı hesaplar, gerçek provider credential secret refs, bağlantı testi, varsayılan/yedek hesap ve OAuth2/SMTP AUTH yetenekleri `SMTP_MAILPIT_DESIGN.md` kapsamında. Kabul: mock provider ekleme ve yeni hesap UI/API üzerinden tanımlama.

## PHASE-04 — SMS & Email Channels
SMS send/status/callback, SMTP TLS/auth, e-posta API adapter, sender identity, attachments policy, DKIM/SPF/DMARC kurulum rehberi, provider-specific error mapping. Mailpit yalnızca dev/test için; gerçek SMTP production adapter ayrıdır. Ayrıntılar: `SMTP_MAILPIT_DESIGN.md`. Kabul: sandbox uçtan uca gönderim, teslim durumları ve güvenlik testleri.

## PHASE-05 — Notification Core
Notification API, event/outbox, templates TR/EN, variables/schema validation, preview, per-user preferences, transactional/marketing separation, consent, opt-out, quiet hours, scheduling, bulk, in-app inbox. Kabul: idempotent send, template versioning, izin testleri.

## PHASE-06 — Delivery Orchestration
RabbitMQ durable queue, worker, retry/backoff/jitter, DLQ, throttling, provider routing/fallback, webhooks signature verification, callback dedup, rate limiting. Kabul: fault injection, duplicate-send prevention, recovery drills.

## PHASE-07 — Credits, Quota & Usage
Provider balance API sync, local credit ledger, tenant/project quotas, cost estimation, alerts, manual adjustment with approval, provider top-up only if officially supported, reconciliation, currency/tax placeholders. Kabul: ledger concurrency/idempotency, balance discrepancy alerts.

## PHASE-08 — Admin Console & Embeddable UI
Standalone Next.js admin, reusable @aka/integration-ui React components; providers, SMS, SMTP, balance, templates, send logs, routing, tenants, reports; host auth/locale/theme/menu adapters; accessibility. SMTP Hesapları, SMTP Hesap Tanımı/Test, Gönderim Geçmişi ve Mailpit Test Gelen Kutusu ekran şartnamesi: `SMTP_ADMIN_UI_DESIGN.md`. Kabul: demo embed in isolated BuildingFlow/TraceFlow shells without duplicating business logic.

## PHASE-09 — Java/.NET/TypeScript SDKs
Java Maven SDK, .NET NuGet SDK, TS client; OpenAPI generation plus handwritten ergonomic facades, retries/timeouts, idempotency, auth, correlation, samples, semantic versioning. Kabul: Java Spring Boot ve ASP.NET Core örneklerinden mock notification.

## PHASE-10 — Monitoring, Observability, Audit & Reporting (OTel Collector + Prometheus + Blackbox Exporter)
Amaç: Aka Integration Hub ve entegre Java/.NET projeleri için metrics, logs, traces ve alarm yönetimini, mevcut iş akışlarını bozmadan sağlamak. Ayrıntılar: `OBSERVABILITY_DESIGN.md`, `OTEL_COLLECTOR_DESIGN.md` ve `BLACKBOX_EXPORTER_DESIGN.md`.

Her alt faz: analiz → etki analizi → dosya planı → onay → uygulama → test → dokümantasyon → onay. Bir çalıştırmada yalnızca bir alt faz.

- **10.1 Instrumentation & contracts:** Spring Boot Actuator/Micrometer ve OpenTelemetry SDK; API, worker, RabbitMQ, provider, PostgreSQL, Valkey, HTTP p95/p99, retries, DLQ; metric naming ve cardinality sözleşmeleri. .NET/Java örnek telemetry.
- **10.2 OTel Collector (yeni bağımsız alt faz):** Collector Contrib, OTLP gRPC/HTTP receivers, memory_limiter, resource, attributes/filter, batch processors; metrics/logs/traces için açık ve ayrı pipeline'lar; health endpoint, bounded queue/retry, TLS/auth, resource limits, secret/PII redaction, containerized dev profile. Önce dry-run config validation ve test; üretim kimlik bilgileri repoya yazılmaz.
- **10.3 Prometheus:** Collector'ın Prometheus exporter endpoint'ini scrape etme (ilk tercih), application scrape compatibility; scrape jobs, retention, storage, recording rules, target health, alert rules.
- **10.4 Grafana:** Prometheus/Loki/Tempo datasource provisioning, sürümlü dashboard'lar, rol ve tenant izolasyonu, admin UI'dan güvenli yönlendirme.
- **10.5 Central logging — Loki:** Structured JSON logs → Collector OTLP logs → Loki OTLP ingestion (uyumlu sürüm ve receiver konfigürasyonu); secret/PII masking, retention, trace correlation.
- **10.6 Distributed tracing — Tempo:** API → outbox → worker → provider için W3C tracecontext, messaging propagation, Collector OTLP traces → Tempo, sampling, latency ve error traces.
- **10.7 Alerts — Alertmanager:** Provider down, 5xx/p95, worker/DLQ, collector dropped/refused telemetry, exporter/scrape down, storage pressure, credit thresholds; alarm döngüsü ve self-dependency koruması.
- **10.8 Audit & Reporting:** PostgreSQL'de audit/transaction system-of-record; tenant/project scoped raporlar, CSV/Excel/PDF, SLA/usage/spend; Prometheus audit kaynağı değildir.
- **10.10 Blackbox Exporter — External Health Checks:** HTTP/HTTPS, TCP, DNS, ICMP (izin verilen ortamlarda) probe modülleri; TLS sertifika bitişi, yanıt süresi, DNS çözümleme ve erişilebilirlik; Prometheus multi-target scrape, Grafana service-health dashboard, Alertmanager alarmları. Ayrıntılar: `BLACKBOX_EXPORTER_DESIGN.md`. SSRF ve iç ağ taraması riskine karşı sabit allowlist, özel ağ erişim kısıtları, kullanıcı girdisinden serbest URL almama, yetkili admin değişiklikleri ve audit zorunludur. SMS/SMTP gerçek teslimatını doğrulamaz; provider adapter başarısı ayrı metriklerden izlenir.
- **10.9 Production readiness:** Fault/load/chaos tests, Collector down senaryosu, bounded buffers, sampling, retention, TLS/RBAC, SLO, dashboards, licensing/SBOM, SaaS/self-hosted deployment ve runbook.

Kabul: Java ve .NET örnek akışlarından en az birinde metric/log/trace korelasyonu, Collector kesintisinde ana iş akışının sürmesi, gizli verinin export edilmemesi, alarm ve dashboard testleri, tenant izolasyonu, tek komutla opsiyonel observability profili.

## PHASE-11 — SaaS Commercialization & Self-Hosted
Plans, subscriptions, usage metering, billing integration abstraction, tenant onboarding, isolation options, backups, disaster recovery, regional data policies, tenant export/delete, upgrade/install scripts, commercial terms/legal review. Kabul: SaaS demo tenant + self-hosted clean install, verified OSS notices.

## PHASE-12 — Additional Channels & Integrations
WhatsApp Business via authorized API, web push/mobile push, webhook destinations, provider connectors, optional payment/e-invoice; adapter capability gating. Kabul: two new channel adapters without core refactor.

## PHASE-13 — BuildingFlow / TraceFlow / AkaAI Rollout
Per-app integration adapters, embedded menu and pages, service credentials, domain events (aidat, duyuru; alım, görev; AI alerts), tenant mapping, end-to-end authorization and rollback. Kabul: all three demos isolated and tested; no host app regressions.

## PHASE-14 — Hardening & Release
Pen test checklist, load tests, chaos tests, SLOs, compliance review, API compatibility, documentation, migration guide, release checklist, backup restore drill. Kabul: signed release artifacts, complete SBOM/NOTICE, launch readiness review.

## PHASE-15 — Cache & Distributed Coordination (Valkey)
Valkey (BSD-3-Clause) varsayılan Redis-protokol uyumlu cache; Spring Data Redis/Lettuce, .NET StackExchange.Redis uyumluluğu; tenant/project scoped key naming, TTL, invalidation, cache-aside, stampede prevention, metrics, fail-open/read-through policy; distributed lock yalnızca gerekli işlerde, fencing/idempotency ile. PostgreSQL system of record, RabbitMQ durable delivery broker. Kabul: tenant isolation, stale-cache, failover, restart, cache-down, concurrency testleri. Redis Server alternatifini ancak ilgili sürüm lisans incelemesi ve onayından sonra destekle.

## PHASE-16 — Documentation & Developer Portal
Docusaurus tabanlı sürümlenmiş TR/EN portal; OpenAPI 3.1 + Swagger UI, Java/.NET/TS SDK quickstarts, React embed ve Storybook, SystemAdmin kullanım kılavuzları, provider setup, kontör/bakiye, security, multi-tenancy, runbook, troubleshooting, architecture C4/Mermaid, ADR, release notes, deployment SaaS/self-hosted, backup/restore. Docs-as-code ve CI link/schema/example checks. Kabul: sıfırdan Java ve .NET entegrasyonu yalnızca dokümanlarla demo ortamında çalışır.

Not: PHASE-15 ve PHASE-16 numaraları önceki planla uyumlu ek aşamalardır; ancak Valkey ve docs-as-code altyapısı PHASE-01'de hazırlanmalı, cache kuralları PHASE-03/05/06/07'de ve API belgeleri her fazda uygulanmalıdır.

# Graph Report - aka-integration-hub  (2026-11-02)

## Corpus Check
- 166 files · ~41,806 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: .typed 3, .example 2, (none) 2)

## Summary
- 1282 nodes · 2756 edges · 84 communities (65 shown, 19 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 257 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d1effad2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- deps.py
- admin-host.tsx
- Env
- mailpit
- app.py
- pytest
- SmtpAccountForm.tsx
- client.py
- with
- email/routes.py
- email/service.py
- smtp/service.py
- list_accounts
- SmtpAccountsPage.tsx
- index.ts
- package.json
- smtp/routes.py
- ui-react/package.json
- useTranslation
- adr/README.md
- README.md
- infrastructure.py
- AKA INTEGRATION HUB — PHASES
- compilerOptions
- WorkerSettings
- compilerOptions
- SecretCipher
- conftest_api.py
- integrations.test.tsx
- health.py
- middleware.py
- AKA INTEGRATION HUB — MASTER PROMPT
- httpx
- ApiErrorCode
- logging.py
- [Unreleased]
- AKA INTEGRATION HUB — OBSERVABILITY DESIGN (PHASE-10)
- design-tokens/package.json
- AGENTS — AKA INTEGRATION HUB
- correlation.py
- AKA INTEGRATION HUB — OTEL COLLECTOR DESIGN (V4 / PHASE-10.2)
- SMTP Yönetimi — UI/UX Şartnamesi (V6)
- Mailpit & Gerçek SMTP — Teknik Tasarım (V6)
- compilerOptions
- SmtpAccountForm
- overview.tsx
- problem_response
- test_system_integration.py
- ADR-0013 — Backend dili: Python (FastAPI)
- AKA INTEGRATION HUB — BLACKBOX EXPORTER DESIGN (PHASE-10.10 / V5)
- .__call__
- Valkey / Redis-Compatible Cache Design
- BuildingFlow ve TraceFlow'dan Hub ekranını açmak (PHASE-13)
- Lisans Envanteri (ilk sürüm)
- PHASE-00 — Discovery & License Gate Raporu
- aih_common/__init__.py
- ADR-0001 — Modüler monolit + ayrı worker
- Bağımlılık ve SBOM Politikası
- Codex / Claude Code — Başlangıç
- Tehdit Modeli (STRIDE, ilk sürüm)
- ADR-0002 — Teknoloji yığını ve sürüm pinleri
- ADR-0003 — PostgreSQL / Valkey / RabbitMQ sorumluluk matrisi
- ADR-0004 — Migration aracı: Flyway Community
- ADR-0008 — Bildirim durum makinesi ve kontör defteri
- Documentation & Developer Portal
- ADR-0005 — Multi-tenant izolasyon modeli
- ADR-0006 — Kimlik, RBAC ve API key
- aih-common
- PHASE_STATUS.md
- json
- V2_CHANGELOG.md
- V6_CHANGELOG.md
- en/host-integration.md
- PHASE_EXECUTION_PROTOCOL.md
- CODING_STANDARDS.md
- PERFORMANCE_RULES.md
- SECURITY_STANDARDS.md
- TOKEN_OPTIMIZATION.md

## God Nodes (most connected - your core abstractions)
1. `Env` - 45 edges
2. `useTranslation()` - 31 edges
3. `_base()` - 27 edges
4. `SmtpAccount` - 25 edges
5. `SmtpContext` - 25 edges
6. `_create()` - 24 edges
7. `send_test_email()` - 21 edges
8. `AKA INTEGRATION HUB — PHASES` - 20 edges
9. `create_app()` - 19 edges
10. `list_accounts()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Karar` --references--> `health()`  [INFERRED]
  docs/adr/0012-observability.md → modules/common/src/aih_common/health.py
- `Mevcut Java iskeleti → Python karşılığı` --references--> `ApiErrorCode`  [INFERRED]
  docs/plans/PYTHON_MIGRATION_PLAN.md → modules/common/src/aih_common/problem.py
- `İş paketleri` --references--> `AppShell()`  [INFERRED]
  docs/phases/PHASE_01_PLAN.md → packages/ui-react/src/components/AppShell.tsx
- `PHASE-08 dilimi — SMTP yönetim ekranları` --references--> `HubSessionProvider()`  [INFERRED]
  CHANGELOG.md → packages/ui-react/src/session.tsx
- `send_with_header()` --calls--> `send()`  [INFERRED]
  modules/common/src/aih_common/middleware.py → apps/api/src/aih_api/email/sender.py

## Import Cycles
- None detected.

## Communities (84 total, 19 thin omitted)

### Community 0 - "deps.py"
Cohesion: 0.06
Nodes (27): Database, current_principal(), lookup(), _dev_principal(), _unauthorized(), Principal, Role, Me (+19 more)

### Community 1 - "admin-host.tsx"
Cohesion: 0.05
Nodes (47): AdminHost(), IdpChooser(), isEmbedded(), ReturnLink(), metadata, RootLayout(), HostContext, loadStoredContext() (+39 more)

### Community 2 - "Env"
Cohesion: 0.15
Nodes (42): Env, _key(), _mailpit_messages(), test_deliveries_are_tenant_isolated(), test_failed_send_is_recorded(), test_real_provider_recipient_must_be_safe(), test_send_requires_confirmation_and_idempotency_key(), test_send_test_email_is_captured_by_mailpit() (+34 more)

### Community 3 - "mailpit"
Cohesion: 0.05
Nodes (46): AIH_VALKEY_PASSWORD, MP_MAX_MESSAGES, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, RABBITMQ_DEFAULT_PASS, RABBITMQ_DEFAULT_USER, RABBITMQ_DEFAULT_VHOST (+38 more)

### Community 4 - "app.py"
Cohesion: 0.09
Nodes (15): create_app(), lifespan(), create_management_app(), build_parser(), _csv(), register_tenant(), run_command(), database_url() (+7 more)

### Community 5 - "pytest"
Cohesion: 0.07
Nodes (15): NetworkPolicy, open_socket(), TargetNotAllowed, test_audit_events_are_append_only(), test_dev_mode_cannot_be_enabled_in_prod(), test_allowlist(), test_dev_policy_allows_local_but_still_blocks_metadata_name(), test_resolved_private_address_is_blocked() (+7 more)

### Community 6 - "SmtpAccountForm.tsx"
Cohesion: 0.09
Nodes (33): PHASE-08 dilimi — SMTP yönetim ekranları, createHubClient(), request(), HubApiError, HubClient, HubClientOptions, ListSmtpParams, newIdempotencyKey() (+25 more)

### Community 7 - "client.py"
Cohesion: 0.09
Nodes (11): build_message(), _ms(), send(), SendResult, classify(), smtp_session(), SmtpError, SmtpTarget (+3 more)

### Community 8 - "with"
Cohesion: 0.07
Nodes (35): name, runs-on, steps, concurrency, cancel-in-progress, group, name, runs-on (+27 more)

### Community 9 - "email/routes.py"
Cohesion: 0.10
Nodes (12): AttemptOut, _delivery_out(), DeliveryOut, get_delivery(), list_deliveries(), _mask_recipient(), send_test_email(), SendTestEmail (+4 more)

### Community 10 - "email/service.py"
Cohesion: 0.12
Nodes (11): Base, EmailDelivery, EmailDeliveryAttempt, begin_test_delivery(), check_recipient_allowed(), finish_delivery(), get_delivery(), list_deliveries() (+3 more)

### Community 11 - "smtp/service.py"
Cohesion: 0.18
Nodes (22): record(), SmtpAccount, SmtpConnectionTest, _check_version(), _clear_default(), create(), _decode_cursor(), _encode_cursor() (+14 more)

### Community 12 - "list_accounts"
Cohesion: 0.14
Nodes (13): connection_tests(), create_account(), _etag(), get_account(), list_accounts(), make_default(), _mask(), _out() (+5 more)

### Community 13 - "SmtpAccountsPage.tsx"
Cohesion: 0.17
Nodes (28): ConnectionTest, EmailIntegrationCard(), Filter, filterLabel(), FILTERS, IntegrationsHome(), matchesFilter(), TypeTile() (+20 more)

### Community 14 - "index.ts"
Cohesion: 0.18
Nodes (23): AppShell(), DEFAULT_NAV_ITEMS, LOCALES, NavItem, INTEGRATION_TYPES, IntegrationType, IntegrationTypeId, LoginShell() (+15 more)

### Community 15 - "package.json"
Cohesion: 0.09
Nodes (28): devDependencies, jsdom@30.1.3, @testing-library/jest-dom@7.0.1, @testing-library/react@16.3.3, @types/node@24.10.1, @types/react@19.3.0, @types/react-dom@19.3.0, typescript@5.9.3 (+20 more)

### Community 16 - "smtp/routes.py"
Cohesion: 0.19
Nodes (16): AccountEnvironment, AuthMode, Capability, ProviderType, TlsMode, capabilities(), ApiModel, CapabilityOut (+8 more)

### Community 17 - "ui-react/package.json"
Cohesion: 0.09
Nodes (24): dependencies, @aka/design-tokens@0.1.0, description, exports, ./styles.css, files, @aka/design-tokens, react (+16 more)

### Community 18 - "useTranslation"
Cohesion: 0.16
Nodes (14): EmailDeliveriesRoute(), SmtpAccountsRoute(), ComingSoon(), SectionPage(), DeliveryStatus, EmailDelivery, EmailDeliveriesPage(), STATUSES (+6 more)

### Community 19 - "adr/README.md"
Cohesion: 0.09
Nodes (16): ADR-0007 — API sözleşmeleri, Karar, ADR-0009 — Gömülebilir React UI, Karar, ADR-0010 — Java / .NET / TypeScript SDK stratejisi, Karar, ADR-0011 — Docs-as-code mimarisi, Karar (+8 more)

### Community 20 - "README.md"
Cohesion: 0.10
Nodes (15): Aka Integration Hub — Marka Kılavuzu, Hukuki not, Logo, Renkler, Tipografi, Getting started (local development), Troubleshooting, Başlangıç (Lokal geliştirme) (+7 more)

### Community 22 - "AKA INTEGRATION HUB — PHASES"
Cohesion: 0.10
Nodes (20): AKA INTEGRATION HUB — PHASES, PHASE-00 — Discovery & License Gate, PHASE-01 — Foundation & Branding, PHASE-01R — Backend Python Geçişi (önerildi), PHASE-02 — Identity, Tenant & Project, PHASE-03 — Provider Registry & Adapter SDK, PHASE-04 — SMS & Email Channels, PHASE-05 — Notification Core (+12 more)

### Community 23 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+9 more)

### Community 24 - "WorkerSettings"
Cohesion: 0.22
Nodes (7): main(), _run(), WorkerSettings, Worker, test_readiness_is_down_before_connecting(), test_readiness_is_up_when_rabbit_is_reachable(), RabbitSettings

### Community 25 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, declaration, esModuleInterop, isolatedModules, jsx, lib, module, moduleResolution (+6 more)

### Community 26 - "SecretCipher"
Cohesion: 0.22
Nodes (3): SecretCipher, SecretStore, SecretStoreError

### Community 27 - "conftest_api.py"
Cohesion: 0.27
Nodes (6): env(), keys(), Keys, settings(), StaticResolver, _verifier()

### Community 28 - "integrations.test.tsx"
Cohesion: 0.18
Nodes (12): İş paketleri, Kabul kriterleri, Kapsam dışı, PHASE-01 — Foundation & Branding Uygulama Planı, Host(), ADMIN, FAILING, HEALTHY (+4 more)

### Community 30 - "health.py"
Cohesion: 0.19
Nodes (4): management_app(), health(), ready(), run_checks()

### Community 32 - "AKA INTEGRATION HUB — MASTER PROMPT"
Cohesion: 0.15
Nodes (12): AKA INTEGRATION HUB — MASTER PROMPT, Ayrıntılı kritik kurallar, Cache, broker ve dokümantasyon için zorunlu ek gereksinimler, Değişmez ilkeler, Her fazın teslimatı, İlk çalıştırma komutu, Kapsam, PHASE-10 — Monitoring & Observability (+4 more)

### Community 33 - "httpx"
Cohesion: 0.27
Nodes (5): _app(), Payload, test_unexpected_error_is_problem_without_internal_message(), test_unsafe_correlation_header_is_replaced(), test_validation_error_lists_fields()

### Community 34 - "ApiErrorCode"
Cohesion: 0.18
Nodes (8): Adımlar, Amaç, Açık sorular, Mevcut Java iskeleti → Python karşılığı, PHASE-01R — Backend'in Python'a taşınma planı, Riskler, ApiErrorCode, test_from_status_falls_back_by_class()

### Community 35 - "logging.py"
Cohesion: 0.26
Nodes (4): configure_logging(), _mask(), redact_sensitive(), test_masks_sensitive_keys_including_nested()

### Community 36 - "[Unreleased]"
Cohesion: 0.18
Nodes (10): Changelog, Mimari karar önerileri (kod değişikliği yok), PHASE-00 — Discovery & License Gate, PHASE-01 — Foundation & Branding, PHASE-01R — Backend Python/FastAPI geçişi, PHASE-02 dilimi — Tenant ve kimlik (SMTP için), PHASE-03 dilimi — SMTP hesap tanımı ve bağlantı testi, PHASE-04 dilimi — SMTP test e-postası ve Mailpit (+2 more)

### Community 37 - "AKA INTEGRATION HUB — OBSERVABILITY DESIGN (PHASE-10)"
Cohesion: 0.18
Nodes (10): AKA INTEGRATION HUB — OBSERVABILITY DESIGN (PHASE-10), Entegrasyon mimarisi, Güvenlik ve lisans, Hedef ve sınırlar, İş metrikleri (önerilen adlar), Kabul testleri, Uygulama kuralları, V4 eki (+2 more)

### Community 38 - "design-tokens/package.json"
Cohesion: 0.20
Nodes (9): description, exports, ./tokens.css, ./tokens.json, files, license, name, private (+1 more)

### Community 39 - "AGENTS — AKA INTEGRATION HUB"
Cohesion: 0.22
Nodes (8): AGENTS — AKA INTEGRATION HUB, Cache ve dokümantasyon kontrol listesi, Done kriteri, Observability görevi, Repo taslağı, V4 OTel Collector, Çalışma protokolü, Öncelikli kalite ve token protokolü (v2 ek)

### Community 41 - "correlation.py"
Cohesion: 0.28
Nodes (4): new_id(), reset(), resolve(), sanitize()

### Community 42 - "AKA INTEGRATION HUB — OTEL COLLECTOR DESIGN (V4 / PHASE-10.2)"
Cohesion: 0.22
Nodes (8): AKA INTEGRATION HUB — OTEL COLLECTOR DESIGN (V4 / PHASE-10.2), Amaç, Codex/Claude uygulama kuralı, Dağıtım, Güvenlik / KVKK, Kabul testleri, Receiver / processor / exporter tasarımı, Referans akış

### Community 43 - "SMTP Yönetimi — UI/UX Şartnamesi (V6)"
Cohesion: 0.22
Nodes (8): Ekran 1: SMTP Hesapları (`/admin/email/providers`), Ekran 2: SMTP Hesap Tanımı (`/admin/email/providers/new`, `/:id/edit`), Ekran 3: E-posta Gönderim Geçmişi (`/admin/email/deliveries`), Ekran 4: Test Gelen Kutusu — Mailpit (`/admin/email/test-inbox`), Kabul kriterleri, Ortak UX, SMTP Yönetimi — UI/UX Şartnamesi (V6), Temel karar

### Community 44 - "Mailpit & Gerçek SMTP — Teknik Tasarım (V6)"
Cohesion: 0.22
Nodes (8): API sözleşmesi (OpenAPI 3.1 ile netleştirilecek), Docker Compose — sadece local development örneği, Geliştirme sırası, Güvenlik ve uyumluluk, Mailpit & Gerçek SMTP — Teknik Tasarım (V6), Sorumluluklar, Test matrisi, Örnek veri modeli (öneri, migration öncesi ADR)

### Community 45 - "compilerOptions"
Cohesion: 0.22
Nodes (8): compilerOptions, noEmit, outDir, rootDir, types, exclude, extends, ./tsconfig.json

### Community 46 - "SmtpAccountForm"
Cohesion: 0.32
Nodes (4): EditSmtpAccountRoute(), NewSmtpAccountRoute(), Field(), SmtpAccountForm()

### Community 47 - "overview.tsx"
Cohesion: 0.46
Nodes (5): Overview(), dynamic, HomePage(), fetchSystemInfo(), SystemInfo

### Community 48 - "problem_response"
Cohesion: 0.32
Nodes (6): install_error_handlers(), api_error(), http_error(), validation_error(), current(), problem_response()

### Community 49 - "test_system_integration.py"
Cohesion: 0.43
Nodes (6): test_actuator_is_not_exposed_on_application_port(), test_liveness_is_up(), test_migration_created_installation_record(), test_readiness_is_up_when_postgres_valkey_and_rabbit_are_reachable(), test_system_info_echoes_correlation_id(), test_unknown_path_returns_problem_detail_with_code()

### Community 50 - "ADR-0013 — Backend dili: Python (FastAPI)"
Cohesion: 0.25
Nodes (7): ADR-0013 — Backend dili: Python (FastAPI), Alternatifler, Bağlam, Hedef dizin yapısı, Karar, Sonuçlar, Önerilen Python yığını

### Community 51 - "AKA INTEGRATION HUB — BLACKBOX EXPORTER DESIGN (PHASE-10.10 / V5)"
Cohesion: 0.25
Nodes (7): AKA INTEGRATION HUB — BLACKBOX EXPORTER DESIGN (PHASE-10.10 / V5), Amaç, Claude Code / Codex çalışma disiplini, Entegrasyon, Güvenlik sınırları, Kabul kriterleri, Uygulama sırası

### Community 52 - ".__call__"
Cohesion: 0.25
Nodes (3): bind(), send_with_header(), _path()

### Community 53 - "Valkey / Redis-Compatible Cache Design"
Cohesion: 0.29
Nodes (6): Karar, Riskler ve testler, SDK, Sorumluluklar, Tasarım, Valkey / Redis-Compatible Cache Design

### Community 54 - "BuildingFlow ve TraceFlow'dan Hub ekranını açmak (PHASE-13)"
Cohesion: 0.29
Nodes (6): 1. Keycloak, 2. Hub tenant kayıtları, 3. Hub admin web (`apps/admin-web/.env`), 4. Host uygulamalar, BuildingFlow ve TraceFlow'dan Hub ekranını açmak (PHASE-13), Güvenlik notları

### Community 55 - "Lisans Envanteri (ilk sürüm)"
Cohesion: 0.29
Nodes (6): İlk SBOM taraması (2026-10-15, PHASE-01), Lisans Envanteri (ilk sürüm), Marka varlıkları, Reddedilen / engelli, Uygulama bağımlılıkları (doğrudan), Çalışma zamanı servisleri (container image)

### Community 56 - "PHASE-00 — Discovery & License Gate Raporu"
Cohesion: 0.29
Nodes (6): Kabul kriterleri, Kapsam (onaya sunulan), Maliyet modeli (taslak), PHASE-00 — Discovery & License Gate Raporu, Risk listesi, Teslimatlar

### Community 58 - "ADR-0001 — Modüler monolit + ayrı worker"
Cohesion: 0.33
Nodes (5): ADR-0001 — Modüler monolit + ayrı worker, Alternatifler, Bağlam, Karar, Sonuçlar

### Community 59 - "Bağımlılık ve SBOM Politikası"
Cohesion: 0.33
Nodes (5): Bağımlılık ve SBOM Politikası, CI, Engelli (kullanıcı/hukuk onayı olmadan eklenemez), İnceleme gerektirir (CI uyarı verir, PR'da gerekçe istenir), İzin listesi (otomatik geçer)

### Community 60 - "Codex / Claude Code — Başlangıç"
Cohesion: 0.33
Nodes (5): Codex / Claude Code — Başlangıç, Prometheus / Monitoring fazı, V4 notu, V5 Monitoring güncellemesi, V6 — SMTP yönetimi ve Mailpit

### Community 61 - "Tehdit Modeli (STRIDE, ilk sürüm)"
Cohesion: 0.33
Nodes (5): Açık noktalar, Güven sınırları, Tehdit Modeli (STRIDE, ilk sürüm), Tehditler ve önlemler, Varlıklar

### Community 62 - "ADR-0002 — Teknoloji yığını ve sürüm pinleri"
Cohesion: 0.40
Nodes (4): ADR-0002 — Teknoloji yığını ve sürüm pinleri, Alternatifler, Karar, Notlar

### Community 63 - "ADR-0003 — PostgreSQL / Valkey / RabbitMQ sorumluluk matrisi"
Cohesion: 0.40
Nodes (4): ADR-0003 — PostgreSQL / Valkey / RabbitMQ sorumluluk matrisi, Karar, Sonuçlar, Valkey vs Redis lisans karşılaştırması

### Community 64 - "ADR-0004 — Migration aracı: Flyway Community"
Cohesion: 0.40
Nodes (4): ADR-0004 — Migration aracı: Flyway Community, Alternatifler, Bağlam, Karar

### Community 65 - "ADR-0008 — Bildirim durum makinesi ve kontör defteri"
Cohesion: 0.40
Nodes (4): ADR-0008 — Bildirim durum makinesi ve kontör defteri, Bildirim durumları, Defter, Kontör kavramları (birbirine karıştırılmaz)

### Community 66 - "Documentation & Developer Portal"
Cohesion: 0.40
Nodes (4): Bilgi mimarisi, Documentation & Developer Portal, Hedef, Kalite kapısı

### Community 67 - "ADR-0005 — Multi-tenant izolasyon modeli"
Cohesion: 0.50
Nodes (3): ADR-0005 — Multi-tenant izolasyon modeli, Karar, Sonuçlar

### Community 68 - "ADR-0006 — Kimlik, RBAC ve API key"
Cohesion: 0.50
Nodes (3): ADR-0006 — Kimlik, RBAC ve API key, Alternatifler, Karar

### Community 69 - "aih-common"
Cohesion: 0.83
Nodes (4): aih-api, aih-common, aih-worker, aka-integration-hub

## Knowledge Gaps
- **1 isolated node(s):** `./tsconfig.json`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 562 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Karar` connect `deps.py` to `health.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `Env` (e.g. with `Infrastructure` and `test_deliveries_are_tenant_isolated()`) actually correct?**
  _`Env` has 39 INFERRED edges - model-reasoned connections that need verification._
- **What connects `./tsconfig.json` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `deps.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0567287784679089 - nodes in this community are weakly interconnected._
- **Why does `info()` connect `deps.py` to `smtp/service.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SmtpAccount` (e.g. with `begin_test_delivery()` and `check_recipient_allowed()`) actually correct?**
  _`SmtpAccount` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `admin-host.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05245901639344262 - nodes in this community are weakly interconnected._
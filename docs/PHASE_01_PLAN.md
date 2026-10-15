# PHASE-01 — Foundation & Branding Uygulama Planı

## İş paketleri
1. **Repo iskeleti:** Maven reactor (`pom.xml`), `modules/common`, `apps/api`, `apps/worker`; npm workspaces
   (`apps/admin-web`, `packages/ui-react`, `packages/design-tokens`).
2. **Backend:** Spring Boot 4.1.1 / Java 21. API: Web, Actuator (liveness/readiness), Data JPA, Flyway, Valkey
   (Spring Data Redis) ve RabbitMQ sağlık göstergeleri, `X-Correlation-Id` filtresi, RFC 9457 hata işleyici,
   `GET /v1/system/info`. Worker: AMQP bağlantısı + health. İlk migration: `platform.schema_info`.
3. **Local Docker:** `infra/docker/compose.yaml` — PostgreSQL 17.6, Valkey 8.1.4, RabbitMQ 4.1.4 (varsayılan),
   Mailpit (`dev-mail` profili). Portlar yalnızca `127.0.0.1`. Sürümler `.env.example`'da pinli, secret yok.
4. **Web:** Next.js 16 admin kabuğu; `@aka/integration-ui` içinde `AkaIntegrationProvider`, `AppShell`, TR/EN
   sözlükleri, light/dark; geliştirme amaçlı login shell (PHASE-02'de OIDC'ye bağlanır).
5. **Marka:** özgün A-akış logo SVG (renkli, monochrome, dark, light), favicon, design tokens (CSS + JSON), marka kılavuzu.
6. **CI:** GitHub Actions — Maven build + test (Testcontainers), web lint/typecheck/test/build, CycloneDX SBOM,
   Markdown link kontrolü.
7. **Dokümantasyon:** README (TR), `docs/guides/{tr,en}/getting-started.md`, `docs/PHASE_STATUS.md`, CHANGELOG.

## Kabul kriterleri
- `make up` (veya `docker compose -f infra/docker/compose.yaml up -d`) + `mvn -pl apps/api spring-boot:run` ile lokal start.
- `/actuator/health/readiness` DB + Valkey + RabbitMQ ile `UP`.
- Testcontainers ile sağlık entegrasyon testi geçer.
- Admin kabuğu TR/EN ve light/dark arasında geçiş yapar, klavye ile gezilebilir.
- Marka varlıkları SVG olarak repoda.

## Kapsam dışı
Gerçek kimlik doğrulama (PHASE-02), tenant tabloları, provider/notification domain'i, Docusaurus portalı (PHASE-16).

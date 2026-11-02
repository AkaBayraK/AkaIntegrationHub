# Changelog

## [Unreleased]
### PHASE-04 dilimi — SMTP test e-postası ve Mailpit
- `POST /v1/tenants/{tenantId}/smtp-accounts/{accountId}/send-test-email`: `confirm: true` ve `Idempotency-Key` zorunlu;
  aynı anahtar + aynı istek → aynı kayıt (ikinci gönderim yok), farklı istek → 409.
- Test alıcısı kısıtı: kendi adresiniz, gönderen alan adı veya `AIH_SMTP_TEST_RECIPIENT_ALLOWLIST`; Mailpit hesapları serbest.
- `email.deliveries` / `email.delivery_attempts` (RLS); durumlar `sending` → `accepted_by_smtp` / `failed`
  (SMTP kabulü teslimat kanıtı değildir); `GET .../email-deliveries` ve `.../{deliveryId}`.
- Gönderim, kayıt transaction'ı commit edildikten sonra yapılır; sonuç ayrı transaction'da işlenir ve audit'e yazılır.

### PHASE-03 dilimi — SMTP hesap tanımı ve bağlantı testi
- `provider.smtp_accounts`, `provider.smtp_connection_tests`, şifreli `provider.secrets` (Fernet, anahtar rotasyonlu `AIH_SECRET_KEYS`).
- PostgreSQL RLS (`FORCE`) + transaction'a özel `aih_app` rolü: tenant bağlamı olmadan satır görünmez.
- `/v1/provider-types/smtp` (capability discovery) ve `/v1/tenants/{tenantId}/smtp-accounts` (liste/oluştur/oku/güncelle,
  `secret` rotasyonu, `make-default`, `test-connection`, `connection-tests`); ETag/If-Match, cursor sayfalama.
- Secret asla geri okunmaz; Viewer'da host/kullanıcı adı maskeli; tüm değişiklikler audit'e yazılır.
- İş kuralları: production'da TLS zorunlu, Mailpit yalnız test, port/TLS uyumu, tek varsayılan hesap (DB unique index).
- SSRF koruması: host biçimi, port izinleri, DNS sonrası tüm IP'lerin kontrolü, doğrulanan IP'ye bağlanma (rebinding koruması).
- Adım bazlı bağlantı testi (DNS/TCP/TLS/greeting/AUTH); sağlayıcı ham yanıtı yerine sınıflandırılmış hata kodu.

### PHASE-02 dilimi — Tenant ve kimlik (SMTP için)
- `tenancy.tenants`, `tenancy.identity_providers` (OIDC issuer → tenant eşlemesi), `audit.audit_events` (append-only trigger).
- OIDC/JWT doğrulama: yalnız kayıtlı issuer'lar, JWKS kayıttan (token'dan değil), RS/ES/PS algoritmaları, `azp`/`aud` istemci kontrolü.
- Tenant ve roller token claim'inden değil issuer kaydından türetilir; IdP rolleri → `PlatformAdmin`/`TenantAdmin`/`Viewer`.
- `GET /v1/me`; tenant path kapsamı (`require(permission)`: yabancı tenant → 404, izin yok → 403).
- `aih-api register-tenant` komutu; yalnız local/test için `X-AIH-Dev-User` geliştirici kimliği; CORS origin ayarı.

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

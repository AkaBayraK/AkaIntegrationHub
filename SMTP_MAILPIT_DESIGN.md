# Mailpit & Gerçek SMTP — Teknik Tasarım (V6)

## Sorumluluklar
- Gerçek SMTP: tenant/proje bazlı sağlayıcı ayarları, STARTTLS/implicit TLS, sağlayıcıya göre OAuth2/SMTP AUTH, sender doğrulaması, gönderim, retry/fallback, audit ve kullanım metrikleri.
- Mailpit: yalnızca dev/test ortamlarında e-posta yakalama ve HTML/plain-text/ek görüntüleme; gerçek SMTP sağlayıcısı yerine production'da kullanılmaz.
- Blackbox Exporter: SMTP endpoint TCP/TLS erişilebilirliği izleyebilir, fakat gerçek teslimatı kanıtlamaz. Gerçek SMTP AUTH testi kontrollü uygulama testinden gelir.

## Örnek veri modeli (öneri, migration öncesi ADR)
- `smtp_accounts`: id UUID, tenant_id, project_id nullable, name, provider_type, host, port, tls_mode, auth_mode, username, secret_ref, sender_address, sender_name, reply_to, environment, enabled, is_default, priority, version, created_at/by, updated_at/by.
- `smtp_connection_tests`: id, account_id, tenant_id, test_type, outcome, error_code, duration_ms, created_at/by; hassas ham cevap saklanmaz.
- `email_deliveries`: id, tenant_id, project_id, account_id, message_id, correlation_id, idempotency_key, status, attempt_count, last_error_code, created_at, updated_at; içerik/ekler ayrı kontrollü saklama politikası.
- `email_delivery_attempts`: id, delivery_id, account_id, attempt_no, smtp_response_class, outcome, duration_ms, created_at.
- Tek aktif varsayılan hesap için tenant+project+environment bazlı DB constraint/transaction; secret rotation ve optimistic locking.

## API sözleşmesi (OpenAPI 3.1 ile netleştirilecek)
- `GET/POST /v1/tenants/{tenantId}/smtp-accounts`
- `GET/PATCH /v1/tenants/{tenantId}/smtp-accounts/{id}`
- `POST /v1/tenants/{tenantId}/smtp-accounts/{id}/test-connection`
- `POST /v1/tenants/{tenantId}/smtp-accounts/{id}/send-test-email`
- `POST /v1/tenants/{tenantId}/smtp-accounts/{id}/make-default`
- `GET /v1/tenants/{tenantId}/email-deliveries`
- `GET /v1/tenants/{tenantId}/email-deliveries/{id}`
- TenantId path parametresi yetki kaynağı değildir: kimlik ve sunucu scope kontrolü zorunlu. Test e-posta alıcısı allowlist/role kısıtlıdır.

## Docker Compose — sadece local development örneği
```yaml
services:
  mailpit:
    image: axllent/mailpit:${MAILPIT_VERSION:?pin-version}
    profiles: ["dev-mail"]
    ports:
      - "127.0.0.1:8025:8025"
      - "127.0.0.1:1025:1025"
    environment:
      MP_MAX_MESSAGES: "5000"
    command: ["--database", "/data/mailpit.db"]
    volumes:
      - mailpit_data:/data
volumes:
  mailpit_data:
```
`MAILPIT_VERSION` onaylı sabit sürümle `.env` içinde tanımlanır; sürüm ve lisans PHASE-00/14 gate ile doğrulanır. Container içi SMTP hedefi `mailpit:1025`, Mac'ten `127.0.0.1:1025`; web UI `127.0.0.1:8025`. Compose profile üretimde etkinleştirilmez. Üretimde dev portları yayınlanmaz.

## Geliştirme sırası
- PHASE-03: SMTP hesap kayıtları, provider capability, credential secret refs, tenant izinleri, test bağlantısı.
- PHASE-04: Gerçek SMTP adapter, TLS/OAuth2, gönderim, Mailpit sandbox adapter, test email, provider error mapping.
- PHASE-06: retry/fallback/idempotency, rate limits, queue; SMTP kabulünü teslimat olarak raporlama.
- PHASE-08: 4 ekranın tasarımı ve uygulaması; storybook; tenant RBAC.
- PHASE-10: SMTP bağlantı testleri, error rate, send latency, Grafana; credential/PII metrik etiketi değildir.
- PHASE-13: TraceFlow/BuildingFlow mevcut ekranlarını koruyarak SDK/API bağlantısı.

## Güvenlik ve uyumluluk
- TLS ve server certificate verification açık; production plaintext SMTP yok; SMTP AUTH/OAuth2 seçenekleri sağlayıcı politikalarına göre.
- Mailpit web arayüzü ve API'si herkese açık internetten erişilemez; örnek e-postalarda gerçek kişisel veri kullanma.
- Provider secrets log, trace, response ve audit'e yazılmaz. SMTP host/port tenant kullanıcıları tarafından serbestçe iç ağ taraması amacıyla kullanılamaz: egress policy, DNS/IP doğrulama, private IP engeli/istisna onayı ve SSRF testleri.
- SMTP SPF/DKIM/DMARC domain setup rehberi; mail reputation ve teslim edilebilirlik garantisi yok.
- SaaS/self-hosted lisans, tedarikçi kullanım şartları ve deployment güvenlik incelemesi.

## Test matrisi
- Tenant isolation, create/edit/default/fallback, disabled provider, secret rotation, concurrency/version, auth errors, TLS cert errors, network timeout, rate-limit, SMTP 4xx/5xx, retry/DLQ, duplicate prevention, Mailpit HTML/attachment assertions, production fail-closed guard, mobile responsive UI.

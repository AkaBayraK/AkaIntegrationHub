# ADR-0007 — API sözleşmeleri

**Durum:** Önerildi · **Faz:** PHASE-00

## Karar
- **API-first, OpenAPI 3.1.** Sözleşme `docs/api/openapi.yaml` altında elle yazılır ve kaynak doğrudur; springdoc
  çıktısı CI'da sözleşmeyle karşılaştırılır (drift testi, PHASE-02).
- **Versiyonlama:** URL yolu `/v1/...`. Kırıcı değişiklik yeni major sürüm gerektirir; eski sürüm en az 12 ay desteklenir.
- **Kaynak adları:** çoğul, kebab-case: `/v1/tenants/{tenantId}/smtp-accounts/{id}`.
- **Hatalar:** RFC 9457 `application/problem+json`. Ek alanlar: `code` (makine okunur, `AIH-<ALAN>-<NNN>`),
  `correlationId`, doğrulama hatalarında `errors[]`. Stack trace veya secret asla dönmez.
- **Idempotency:** yan etkili `POST` uçlarında `Idempotency-Key` başlığı (gönderim uçlarında zorunlu). Anahtar
  `(tenant_id, key)` tekil; aynı anahtar + farklı gövde → `409`; aynı anahtar + aynı gövde → ilk yanıt tekrar döner. 24 saat saklanır.
- **Korelasyon:** `X-Correlation-Id` başlığı kabul edilir veya üretilir, yanıtta döner, log MDC'ye ve W3C `traceparent`'a bağlanır.
- **Sayfalama:** cursor bazlı `?limit=&cursor=`; `limit` en fazla 200, varsayılan 50. Yanıt: `{ items, nextCursor }`.
- **Optimistic concurrency:** güncellenebilir kaynaklarda `ETag`/`If-Match` (`version` alanı).
- **Zaman:** ISO-8601 UTC; para birimi ISO-4217 + minor unit tam sayı.
- HTTP durumları: 200/201/202 (asenkron kabul)/204/400/401/403/404/409/412/422/429/5xx.

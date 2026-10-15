# ADR-0003 — PostgreSQL / Valkey / RabbitMQ sorumluluk matrisi

**Durum:** Önerildi · **Faz:** PHASE-00 · **İlgili:** `CACHE_VALKEY_DESIGN.md`

## Karar

| Veri / iş | PostgreSQL | RabbitMQ | Valkey |
|---|---|---|---|
| Tenant, proje, kullanıcı, rol | **Otoritatif** | — | Kısa TTL'li yetki cache'i |
| Provider hesapları, secret ref | **Otoritatif** | — | Secret içermeyen config cache |
| Bildirim ve teslim durumu | **Otoritatif** | — | — |
| Outbox | **Otoritatif** | Yayın hedefi | — |
| Gönderim işi, retry, DLQ | Durum kaydı | **Kalıcı kuyruk** | — |
| Idempotency anahtarı | **Otoritatif** (unique constraint) | — | Hızlı ön kontrol (opsiyonel) |
| Kontör defteri | **Otoritatif, append-only** | — | Asla |
| Rate limit sayaçları | — | — | **Sahip** (kaybı kabul edilebilir) |
| Audit | **Otoritatif, append-only** | — | Asla |
| Dağıtık kilit | Fencing token kaynağı | — | Kısa süreli kilit (yalnızca gerektiğinde) |

- Valkey Pub/Sub kalıcı bildirim kuyruğu olarak **kullanılmaz**.
- Cache anahtarı: `aka:{env}:{tenantId}:{projectId}:{domain}:{id}:v{schemaVersion}` (Valkey tarafında `projectId`
  yoksa `_`). Anahtar üretimi tek bir `CacheKeyFactory` üzerinden yapılır; tenant scope sunucu tarafındaki güvenlik
  bağlamından alınır, istemci girdisinden alınmaz.
- Cache-down davranışı: read-through/fail-open (doğrudan PostgreSQL), rate limit için fail-closed değil
  konservatif yerel limit. Finansal işlemlerde cache hiçbir koşulda karar verici değildir.

## Valkey vs Redis lisans karşılaştırması

| Ürün | Sürüm | Lisans | Ticari self-hosted dağıtım | Karar |
|---|---|---|---|---|
| Valkey | 8.1.x | BSD-3-Clause | İzin verici; atıf | **Varsayılan** |
| Redis OSS | ≤ 7.2.4 | BSD-3-Clause | İzin verici, ancak bakım sonu | Kullanılmaz |
| Redis | 7.4 – 7.8 | RSALv2 / SSPLv1 | Kısıtlı | Reddedildi |
| Redis | 8.x | RSALv2 / SSPLv1 / AGPLv3 (seçmeli) | AGPL yükümlülükleri | Hukuk onayı olmadan kullanılmaz |

İstemci tarafı: Java Lettuce (MIT) / Spring Data Redis (Apache-2.0), .NET StackExchange.Redis (MIT). Valkey
protokol uyumluluğu PHASE-15'te gerçek entegrasyon testleriyle doğrulanır; PHASE-01'de yalnızca bağlantı sağlık kontrolü.

## Sonuçlar
Kayıp-tolere eden veri dışında hiçbir şey Valkey'e bağımlı değildir. Valkey yokken sistem yavaşlar ama doğru çalışır.

# Valkey / Redis-Compatible Cache Design

## Karar
Varsayılan Valkey (BSD-3-Clause). Redis Server yalnızca sürüm bazında lisans ve dağıtım değerlendirmesinden sonra opsiyonel.

## Sorumluluklar
- PostgreSQL: provider config, ledger, notification, idempotency, audit; authoritative.
- RabbitMQ: durable dispatch, retry/DLQ, asynchronous processing.
- Valkey: cache, geçici sayaçlar, rate limiting, gerektiğinde kısa süreli koordinasyon.

## Tasarım
Key: `aka:{env}:{tenantId}:{projectId}:{domain}:{id}:v{schemaVersion}`. Hassas veri ve credential saklama. TTL sınıfa göre; değişiklikte invalidation; cache-aside; stampede önleme; metrikler. Tenant scope hem key'de hem authorization katmanında doğrulanır.

## Riskler ve testler
Cache down, restart, stale values, TTL, tenant collision, race conditions, failover, reconnect, memory pressure. Finansal quota/ledger işlemlerinde atomiklik PostgreSQL transaction ile sağlanır; cache sayaçları tek başına mali doğruluk garantisi vermez. Dağıtık kilitlerde fencing token/idempotency gerekir.

## SDK
Java Spring Data Redis/Lettuce, .NET StackExchange.Redis uyumluluğu gerçek entegrasyon testleriyle doğrulanır.

# Architecture Decision Records

Her ADR: Bağlam → Karar → Sonuçlar → Alternatifler → Durum. Durum değerleri: `Önerildi`, `Kabul`, `Değiştirildi`, `Reddedildi`.
Kabul edilmiş bir ADR değiştirilmez; yerine yenisi yazılır ve eskisi `Değiştirildi` olarak işaretlenir.

| No | Başlık | Durum |
|---|---|---|
| [0001](0001-modular-monolith.md) | Modüler monolit + ayrı worker | Önerildi |
| [0002](0002-technology-stack.md) | Teknoloji yığını ve sürüm pinleri | Önerildi |
| [0003](0003-store-cache-broker-matrix.md) | PostgreSQL / Valkey / RabbitMQ sorumluluk matrisi | Önerildi |
| [0004](0004-database-migrations.md) | Migration aracı: Flyway Community | Önerildi |
| [0005](0005-multi-tenancy-isolation.md) | Multi-tenant izolasyon modeli | Önerildi |
| [0006](0006-identity-and-access.md) | Kimlik, RBAC ve API key | Önerildi |
| [0007](0007-api-conventions.md) | API sözleşmeleri (OpenAPI 3.1, problem details, idempotency) | Önerildi |
| [0008](0008-notification-and-credit-model.md) | Bildirim durum makinesi ve kontör defteri | Önerildi |
| [0009](0009-embeddable-ui.md) | Gömülebilir React UI | Önerildi |
| [0010](0010-sdk-strategy.md) | Java / .NET / TypeScript SDK stratejisi | Önerildi |
| [0011](0011-docs-as-code.md) | Docs-as-code mimarisi | Önerildi |
| [0012](0012-observability.md) | Gözlemlenebilirlik yaklaşımı | Önerildi |

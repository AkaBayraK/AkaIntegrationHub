# ADR-0010 — Java / .NET / TypeScript SDK stratejisi

**Durum:** Önerildi · **Faz:** PHASE-00 (uygulama PHASE-09)

## Karar
- Alt katman OpenAPI 3.1 sözleşmesinden **üretilir** (OpenAPI Generator, Apache-2.0); üstte elle yazılmış ergonomik facade.
- **Java:** Java 21 baseline, `java.net.http.HttpClient` (ek HTTP bağımlılığı yok), Jackson; Spring Boot starter ayrı artefakt.
  Maven koordinatı `io.akahub:aih-client` (groupId alan adı tescilinden sonra kesinleşir — DOĞRULANMADI).
- **.NET:** .NET 8 LTS hedef, `HttpClient` + `IHttpClientFactory`, `CancellationToken` her çağrıda; NuGet `Aka.IntegrationHub.Client`.
- **TypeScript:** `packages/ts-client`, fetch tabanlı, bağımlılıksız; UI paketi de bunu kullanır.
- Ortak davranış: idempotency key otomatik üretimi, `X-Correlation-Id` yayılımı, yalnızca idempotent çağrılarda
  exponential backoff + jitter retry, zaman aşımı varsayılanları, problem-details hatalarının tipli istisnaya dönüşümü.
- Semantic versioning; SDK major sürümü API major sürümüyle hizalı.

# AKA INTEGRATION HUB — MASTER PROMPT

## Ürün
Aka Integration Hub (AIH): bağımsız, multi-tenant, self-hosted veya SaaS olarak çalışabilen entegrasyon ve bildirim platformu. BuildingFlow, TraceFlow, AkaAI ve üçüncü taraf Java/.NET projeleri kullanır. Repo: `aka-integration-hub`. Ürün dili Türkçe/İngilizce. Marka: lacivert, mavi, turkuaz; bağlantı/akış çağrıştıran özgün A ikonu. Görsel referans marka varlığıdır; kodlanabilir SVG varyantlarını özgün olarak üret.

## Değişmez ilkeler
1. Kodlamadan önce repository'yi analiz et; mevcut dosyaları izinsiz silme veya çalışan davranışı bozma.
2. Her seferinde yalnızca istenen fazı uygula. Faz sonunda dur ve kullanıcı onayını bekle.
3. Konsolda Türkçe ilerleme bildir: [FAZ], [ADIM], [DURUM], [DOSYA], [TEST], [RİSK], [SONRAKİ]. Gerçek token kotasını bilmiyorsan tahmin etme.
4. Projeler arası tenant/project izolasyonunu API, DB, queue, log, şablon, secret, kota ve UI seviyesinde zorunlu kıl. Client'ın gönderdiği tenant id'ye kör güvenme.
5. API-first: OpenAPI 3.1; Java 21 ve .NET 8+ istemci SDK'ları; idempotency key, correlation id, pagination, versioning ve tutarlı problem-details hataları.
6. SaaS ve self-hosted dağıtımı destekle; müşteri ortamında sağlayıcı credential'larını izole et; sırrı loglama.
7. Önce tek deploy edilebilir modüler monolit + ayrı worker opsiyonu; kanıtlanmış ihtiyaç halinde mikroservise ayrılabilecek sınırlar.
8. Ticari kullanımda izin verilen lisanslara öncelik ver (Apache-2.0, MIT, BSD, PostgreSQL License vb.). Ürün/versiyon/dağıtım biçimine göre her bağımlılığın lisansını ve NOTICE yükümlülüğünü doğrula. Copyleft, SSPL, BSL, AGPL, ticari lisans ve provider sözleşmelerini otomatik olarak uygun sayma. Lisans konusunda sıfır risk garantisi verme.
9. UI React bileşen paketi olarak Next.js host uygulamalarına gömülebilmeli; bağımsız admin web de aynı bileşenleri kullanmalı. Host uygulamanın auth, tema, dil, navigasyon ve tenant bağlamıyla entegre olmalı. iframe temel çözüm değildir.
10. Gerçek sağlayıcı credential'ı olmadan mock/sandbox adapter ile uçtan uca test edilebilir olmalı.

## Önerilen yığın (karar ADR ile doğrulanacak)
Backend Java 21, Spring Boot, Spring Security, Spring Data JPA, PostgreSQL; Next.js + TypeScript + React + Tailwind + erişilebilir UI bileşenleri; Keycloak OIDC opsiyonel kimlik sağlayıcı; RabbitMQ veya uygun lisanslı alternatif; Valkey cache; OpenTelemetry + Prometheus + Grafana; Docker Compose; OpenAPI; Maven Central Java SDK ve NuGet .NET SDK. Kütüphane sürümlerini resmi kaynaklarla doğrula, otomatik en yeniye yükseltme.

## Kapsam
Provider registry, provider capability discovery, tenant/proje credential konfigürasyonu, SMS, SMTP ve e-posta API, WhatsApp, push, in-app, webhook, notification templates, preferences, consent, opt-out, quiet hours, locale/timezone, scheduling, batch, event-driven dispatch, retries/DLQ, fallback, quota/credit/cost, provider balance sync, top-up capability (yalnızca API destekliyorsa), usage ledger, billing, subscriptions, audit, observability, reports, systemadmin console, embed UI, Java/.NET SDK.

## Ayrıntılı kritik kurallar
- Kontör: provider gerçek bakiyesi, yerel tahmini bakiye ve müşteri platform kotası ayrı kavramlardır. Muhasebe defteri append-only ve idempotent olmalı. Manuel kontör ekleme, sağlayıcıda fiili yükleme değildir.
- Notification: accepted, queued, sent-to-provider, delivered, failed, cancelled gibi durumları ayrıştır. Provider kabulü teslimat kanıtı değildir. Webhook callback imzasını doğrula; tekrar gelen callback idempotent işlenmeli.
- Retry: transient/permanent hata ayrımı, exponential backoff+jitter, DLQ, duplicate prevention. Fallback'te mükerrer ücretlendirme ve çift gönderim riskini değerlendir.
- İleti onayı: pazarlama ve operasyonel bildirim ayrımı, ülke/kanal bazlı izin ve saklama politikaları; KVKK/GDPR ve yerel SMS mevzuatı hukuk incelemesi gerektirir.
- Sağlayıcı ekleme: mevcut desteklenen adapter'a yeni hesap UI'dan eklenebilir. Tamamen yeni protokol/provider için kontrollü plugin/adapter geliştirme ve deployment gerekir; rastgele kod yükleme yok.
- Auth: OIDC/JWT doğrulama, RBAC+resource-scoped permissions, tenant-scoped service accounts, API key rotation, rate limit, audit. SaaS platform admin ile tenant admin ayrılmalı.
- SaaS billing: plan, seat, usage, invoice, metering; ödeme sağlayıcısı sonradan bağlanabilir. Ürün lisansı ile üçüncü taraf altyapı lisansını karıştırma.

## Her fazın teslimatı
Analiz, ADR, veri modeli, API kontratı, migration, backend, frontend (gerekiyorsa), SDK (gerekiyorsa), unit/integration/e2e test, security tests, lisans tarama sonucu, changelog, demo ve kabul kriterleri. Belirsizlikleri sor; mevcut kodu varsayma.

## İlk çalıştırma komutu
`AGENTS.md`, `PHASES.md` ve bu dosyayı oku. Repository'yi analiz et. SADECE PHASE-00 ve PHASE-01 için analiz/plan üret; henüz uygulama kodu yazma. Türkçe adım adım konsol raporu ver. Riskleri ve lisans kararlarını açıkla. Onayımı bekle.


## Cache, broker ve dokümantasyon için zorunlu ek gereksinimler
- Varsayılan Redis-protokol sunucusu Valkey (BSD-3-Clause). Redis Server ürün/sürüm lisansı ayrıca incelenmeden zorunlu bağımlılık olamaz. Java Spring Data Redis/Lettuce; .NET StackExchange.Redis istemci uyumluluğunu doğrula.
- PostgreSQL otoritatif veri kaynağıdır. Kontör defteri, gönderim durumları, idempotency ve audit kayıtları yalnızca cache'te tutulamaz. RabbitMQ kalıcı mesaj işleme için tercih edilir; Valkey Pub/Sub kalıcı bildirim kuyruğu yerine kullanılmaz.
- Tenant/project anahtar izolasyonu, TTL, invalidation, cache-down fallback, kilit/fencing ve gözlemlenebilirlik için test zorunlu.
- Dokümantasyon birinci sınıf ürün bileşenidir: Docusaurus TR/EN, OpenAPI 3.1, Swagger UI, Storybook, Java/.NET/TypeScript SDK örnekleri, SaaS/self-hosted kurulum, SystemAdmin kılavuzu, ADR, C4/Mermaid ve operasyon runbook'ları. Her faz dokümantasyon ve changelog güncellemesiyle tamamlanır.
- PHASES.md PHASE-15 ve PHASE-16'yı içerir; PHASE-01 temel iskeleti erkenden kurar.

## PHASE-10 — Monitoring & Observability
PHASE-10 için `OBSERVABILITY_DESIGN.md` zorunlu şartnamedir. Prometheus + Grafana + Alertmanager + OpenTelemetry/Tempo + Loki mimarisini uygula; KVKK/PII koruması, tenant izolasyonu, düşük kardinaliteli metrics, monitoring kapalıyken uygulamanın çalışması ve lisans kontrolü zorunludur.


## V6 — SMTP yönetimi ve Mailpit
`SMTP_ADMIN_UI_DESIGN.md` ve `SMTP_MAILPIT_DESIGN.md` dosyalarını incele. Gerçek SMTP tenant bazlı yönetilir; Mailpit yalnızca izole geliştirme/test profilinde çalışır. PHASE-03/04/08 fazlarını sırasıyla analiz et; mevcut kodu değiştirmeden önce onay al.

## v2 — Zorunlu uygulama kapısı
Her geliştirme fazında `AGENTS.md` içindeki v2 kalite kurallarını uygula. Tek faz, hedefli keşif, lisans ve güvenlik kapısı, mevcut ortak kodun yeniden kullanımı, minimal diff, hedefli test ve kısa Türkçe ilerleme zorunludur. Mevcut iş kurallarını ve faz sıralamasını koru. Bu dosyaların varlığı, lisansların veya testlerin fiilen doğrulandığı anlamına gelmez.

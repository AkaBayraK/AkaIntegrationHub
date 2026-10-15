# AKA INTEGRATION HUB — OTEL COLLECTOR DESIGN (V4 / PHASE-10.2)

## Amaç
OpenTelemetry Collector Contrib ile Aka Integration Hub API/worker ve entegre Java/.NET projelerinden metrics, logs ve traces al; doğrula, filtrele, batch işle ve uygun backend'e yönlendir. Collector business data store veya Prometheus alternatifi değildir.

## Referans akış
- Java Spring Boot / .NET SDK: OTLP HTTP 4318 veya gRPC 4317 (internal only) → Collector.
- Metrics: Collector Prometheus exporter (ör. internal 9464) → Prometheus scrape → Grafana.
- Traces: Collector OTLP exporter → Tempo OTLP receiver → Grafana.
- Logs: Collector OTLP HTTP exporter → Loki OTLP endpoint (sürüm/URL doğrulaması) → Grafana.
- Prometheus rules → Alertmanager → bağımsız/fallback uyarı kanalı.
- Collector health ve kendi metrikleri ayrıca izlenir; external-facing telemetry ports varsayılan kapalıdır.

## Receiver / processor / exporter tasarımı
- Receivers: `otlp` gRPC ve HTTP; gerekmedikçe host üzerinde port publish etme.
- Processors: `memory_limiter` (batch öncesi), `resource` (service.name/environment), `filter` ve/veya `transform` ile hassas alanların kaldırılması, `batch`.
- Exporters: `prometheus` (metrics), `otlp` (Tempo traces), `otlphttp` (Loki logs). Kullanılacak component isimleri ve sürüm uyumluluğu release öncesi doğrulanır.
- Service pipelines: `metrics`, `logs`, `traces` ayrı ayrı tanımlanır; yanlış sinyal exporter'a yönlendirilmez.
- Retry/queue: exporter desteğine göre bounded sending queue, exponential retry ve backpressure; yüksek hacimde veri kaybı ve kapasite sınırları raporlanır.
- Sampling: traces için gereksinime göre head sampling; tail sampling ayrı Collector/ölçekleme analizi gerektirir. Hata trace'lerini koruma politikası belirlenir.

## Güvenlik / KVKK
- TLS/mTLS veya güvenli özel ağ + uygun kimlik doğrulama; SaaS tenant izolasyonu için Collector'ın tek başına tenant güvenlik sınırı olmadığı kabul edilir.
- Telefon, e-posta, mesaj içeriği, token, cookie, API key, credentials ve kişisel veriler log/span attribute/metric label'a yazılmaz.
- tenant_id/project_id/user_id/request_id/message_id gibi yüksek kardinaliteli alanlar metric label olamaz. Trace/log içinde gerekli kimlikler varsa maskeleme, erişim ve retention kuralları uygulanır.
- Secret değerleri repoya commit edilmez; endpoint'ler public expose edilmez.

## Dağıtım
- Docker Compose `observability` profili ile opsiyonel servis; Hub monitoring kapalıyken işlevini sürdürür.
- Collector CPU/RAM limits, restart policy, healthcheck, pinned image version, config validation ve shutdown grace period.
- Prod için ayrı network policy, scaling, exporter permissions ve kapasite hesabı; image/lisans/SBOM/CVE kontrolü.

## Kabul testleri
1. Java API ve .NET demo uygulamasından OTLP telemetry alınır.
2. Bir notification isteği için metrics, structured logs ve traces Grafana'da ilişkilendirilir.
3. PII/secret örnekleri export edilmeden maskelenir veya reddedilir.
4. Collector/Loki/Tempo/Prometheus kesintisinde SMS/SMTP/notification iş akışı durmaz.
5. Memory limit ve queue doluluğunda kontrollü backpressure/drop metrikleri gözlenir.
6. Collector dış ağdan erişilemez; yetkisiz erişim reddedilir.
7. Dashboard ve alarm senaryoları otomatik test edilir; tenant A, tenant B'nin raporlarını göremez.
8. Yeni dependency lisansları ve NOTICE/SBOM gözden geçirilir.

## Codex/Claude uygulama kuralı
Önce `MASTER_PROMPT.md`, `AGENTS.md`, `PHASES.md`, `OBSERVABILITY_DESIGN.md` ve bu dosyayı oku. Yalnızca PHASE-10.2 için mevcut repo analizi yap; önerilen değişiklikleri ve testleri Türkçe konsola yaz; mevcut dosyaları değiştirmeden onay bekle. Onay sonrası küçük, testli ve geri alınabilir adımlarla uygula.

# AKA INTEGRATION HUB — OBSERVABILITY DESIGN (PHASE-10)

## Hedef ve sınırlar
Monitoring ayrı bir ürün değildir: Aka Integration Hub altyapı modülüdür. Grafana/Prometheus doğrudan halka açık sunulmaz. Dev ortamında Docker Compose `observability` profili; production ortamında ayrı servis/cluster ve uygun auth/network policy. PHASE-10 mevcut PHASE-00–16 sırasını değiştirmez.

## Önerilen bileşenler
- Spring Boot Actuator + Micrometer Prometheus registry: backend/worker metrics.
- Prometheus: scrape, PromQL, recording/alert rules, time-series retention.
- Grafana: dashboard ve sorgulama, datasource provisioning.
- Alertmanager: alarm yönlendirme, deduplication, silence, escalation.
- OpenTelemetry SDK + Collector: distributed traces, OTLP pipelines.
- Grafana Tempo: trace backend.
- Grafana Loki: yapılandırılmış uygulama logları; güvenli log toplama ajanı/OTel Collector üzerinden gönderim.
- RabbitMQ exporter, PostgreSQL exporter ve Valkey/Redis exporter: ayrı, yetkisi kısıtlı exporter'lar; gerekli olanları aşamalı ekle.

## İş metrikleri (önerilen adlar)
`aka_notifications_sent_total{channel,provider,status}`
`aka_notification_delivery_duration_seconds{channel,provider}` histogram
`aka_provider_requests_total{provider,operation,outcome}`
`aka_provider_request_duration_seconds{provider,operation}` histogram
`aka_worker_jobs_total{job_type,outcome}`
`aka_worker_retries_total{job_type,reason}`
`aka_outbox_pending_messages` gauge
`aka_dlq_messages` gauge
`aka_credit_balance_threshold_events_total{severity}`
`aka_quota_rejections_total{quota_type}`

Yalnızca kontrollü, düşük kardinaliteli label'lar. `tenant_id`, `project_id`, `user_id`, telefon, e-posta, mesaj ID, request ID, token veya provider credential label OLAMAZ. Tenant raporları yetkili PostgreSQL sorguları ve uygun agregasyonla sunulur; Prometheus etiketlerinden tenant verisi sızdırılmaz.

## Entegrasyon mimarisi
`Hub API/Workers -> OTel SDK/Micrometer -> OTel Collector -> Prometheus exporter -> Prometheus (metrics); Collector -> Loki (logs); Collector -> Tempo (traces); Grafana -> Prometheus/Loki/Tempo`.
Collector kullanımı uygulama metriklerinin doğrudan scrape edilmesini zorunlu kılmaz; seçilen tek metric ingestion yolu dokümante edilerek duplicate series önlenir. Collector geçici taşıma/işleme katmanıdır, kalıcı depolama değildir.
`Prometheus rules -> Alertmanager -> authenticated Hub notification webhook -> SMS/SMTP/other providers`.
Alarmın kendisi aynı hatalı sağlayıcıya bağımlı kalmamalı; ayrı fallback ve alarm loop koruması gerekir.

## Güvenlik ve lisans
Tüm bileşen ve exporter sürümleri PHASE-00 lisans kapısından geçer. Grafana OSS, Loki, Tempo, Prometheus, Alertmanager ve kullanılan ajanların ilgili sürüm lisanslarını ayrıca doğrula; AGPL bileşenleri için dağıtım/SaaS yükümlülüklerini hukuk kontrolüne taşı. OSS lisansını ticari kullanımın otomatik olarak koşulsuz serbest olduğu şeklinde yorumlama. Secret'ları env dosyalarında repoya yazma; secret manager/refs kullan. Endpoint'ler private network; Grafana SSO/RBAC; audit trail ve retention politikaları.

## Uygulama kuralları
1. Önce repository'yi analiz et, mevcut telemetry altyapısını bul.
2. Mevcut çalışan modülleri ezme, yeni dosyaları planla ve onay al.
3. Docker Compose profile ile dev ortamı ekle; core uygulama observability kapalıyken de çalışsın.
4. Dashboard'ları JSON provisioning ile sürüm kontrolüne al.
5. Metrik birimleri ve label şemasını dokümante et; testlerle doğrula.
6. Trace/log/metric correlation için örnek akış oluştur.
7. KVKK/PII, yüksek kardinalite, scrape endpoint erişimi ve maliyet/retention testlerini zorunlu kıl.
8. Her alt adımda konsola `[AKA-HUB][PHASE-10][STEP-x][STATUS]` biçiminde Türkçe ilerleme yaz.
9. Alt adım sonunda test, risk ve değişen dosyalar raporu oluştur; onay bekle.

## Kabul testleri
- HTTP 5xx ve p95 latency artışı panoda görünür.
- Provider mock down olduğunda alarm oluşur; retry ve DLQ sayıları güncellenir.
- Bir bildirim için correlation ID ile log ve trace bulunur.
- Yetkisiz kullanıcı metrik endpoint'ine ve tenant raporuna erişemez.
- Hiçbir metrik label/log secret, telefon veya e-posta içermez.
- Prometheus/Grafana/Loki/Tempo kapalıyken ana bildirim akışı devam eder.
- `docker compose --profile observability up -d` ile gerekli servisler (ilgili compose tanımında) ayağa kalkar.

## V4 eki
Collector yapılandırması, pipeline, failure mode ve acceptance kriterleri için `OTEL_COLLECTOR_DESIGN.md` belgesine bak. PHASE-10.2 başlamadan hiçbir mevcut container, env veya endpoint ezilmez.

## V5 eki — Blackbox Exporter
Dışarıdan erişilebilirlik kontrolleri PHASE-10.10 kapsamında `BLACKBOX_EXPORTER_DESIGN.md` belgesinde tanımlıdır. Blackbox, gönderim başarısını veya iş akışının doğruluğunu tek başına kanıtlamaz.

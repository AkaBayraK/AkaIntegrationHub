# ADR-0012 — Gözlemlenebilirlik yaklaşımı

**Durum:** Önerildi · **Faz:** PHASE-00 (temel PHASE-01, tam kapsam PHASE-10) · **İlgili:** `OBSERVABILITY_DESIGN.md`, `OTEL_COLLECTOR_DESIGN.md`

## Karar
- PHASE-01'den itibaren: Spring Boot Actuator `health` (liveness/readiness grupları), yapılandırılmış JSON log,
  `X-Correlation-Id` → MDC. Actuator yalnızca ayrı yönetim portunda (`8081`) ve sadece `health`, `info` açık.
- Metrik etiketi olarak `tenant_id`, `project_id`, `user_id`, telefon, e-posta, mesaj/istek kimliği **kullanılamaz**;
  PHASE-10.1'de kardinalite testleri bunu zorlar.
- Tek metrik toplama yolu: OTel Collector → Prometheus exporter (PHASE-10.2/10.3). Doğrudan scrape yalnızca
  Collector'sız self-hosted kurulum için ve ikisi birlikte açılmaz (duplicate series).
- **Lisans uyarısı:** Grafana, Loki ve Tempo **AGPL-3.0**'dır. Değiştirilmemiş resmi image'ları ayrı servis olarak
  çalıştırmak yaygın bir modeldir; ancak SaaS'ta kullanıcıya sunma ve self-hosted'da müşteriye dağıtma senaryoları
  **hukuk incelemesi** gerektirir. Prometheus/Alertmanager/Blackbox Exporter/OTel Collector Apache-2.0'dır.
- Observability profili kapalıyken ana iş akışı değişmeden çalışır (kabul kriteri).

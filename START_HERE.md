# Codex / Claude Code — Başlangıç

1. Yeni, boş `aka-integration-hub` repository aç.
2. MASTER_PROMPT.md, AGENTS.md, PHASES.md dosyalarını repository köküne koy.
3. Aşağıdaki promptu Codex veya Claude Code'a ver:

> `MASTER_PROMPT.md`, `AGENTS.md` ve `PHASES.md` dosyalarını tamamen oku. Bu ürün BuildingFlow, TraceFlow, AkaAI ve bağımsız Java/.NET müşteri uygulamaları için ticari SaaS + self-hosted entegrasyon/bildirim platformudur. İlk etapta yalnızca PHASE-00 analizi ve PHASE-01 uygulama planını oluştur. Mevcut kodları değiştirme. Teknoloji lisanslarını doğrulamadan bağımlılık seçme. Mimari, modül sınırları, veritabanı, OpenAPI, Java/.NET SDK, embed React UI, güvenlik, multi-tenant izolasyon, kontör ve notification tasarımını ADR olarak yaz. Her adımı Türkçe konsola yaz. Fazların kabul kriterlerini ve risklerini raporla; sonunda durup onayımı bekle.`

4. Onaydan sonra: `Yalnızca PHASE-01'i uygula. Önce değişecek dosyaları ve adımları göster; sonra test et, raporla ve dur.`

Not: Marka adının, domain'in ve logonun ticari marka açısından kullanılabilirliği ayrıca araştırılmalıdır. Görsel tasarım özgün vektör formatına dönüştürülmelidir.


Ek talimat: PHASE-00 sırasında Valkey/Redis lisans karşılaştırması, cache-broker-veritabanı sorumluluk matrisi ve docs-as-code mimarisi de ADR olarak yazılmalıdır. PHASE-01'de Valkey + RabbitMQ + PostgreSQL Docker Compose profili ve dokümantasyon iskeleti planlanmalıdır.

## Prometheus / Monitoring fazı
V3 ile PHASE-10 genişletildi. Önce `OBSERVABILITY_DESIGN.md` ve `PHASES.md` içindeki PHASE-10 bölümünü oku. Fazı çalıştırmak için: `Yalnızca PHASE-10.1 analizini yap. Mevcut kodları değiştirme. Türkçe konsol raporu yaz ve onayımı bekle.`


## V4 notu
PHASE-10.2 için `OTEL_COLLECTOR_DESIGN.md` eklendi. V3 fazları korunmuştur; monitoring altyapısı opsiyonel ve ayrı alt adımlarla uygulanır.

## V5 Monitoring güncellemesi
PHASE-10.10 Blackbox Exporter için `BLACKBOX_EXPORTER_DESIGN.md` dosyasını incele. Mevcut SMS UI korunur; erişilebilirlik testi ile gerçek teslimat durumunu karıştırma.


## V6 — SMTP yönetimi ve Mailpit
`SMTP_ADMIN_UI_DESIGN.md` ve `SMTP_MAILPIT_DESIGN.md` dosyalarını incele. Gerçek SMTP tenant bazlı yönetilir; Mailpit yalnızca izole geliştirme/test profilinde çalışır. PHASE-03/04/08 fazlarını sırasıyla analiz et; mevcut kodu değiştirmeden önce onay al.

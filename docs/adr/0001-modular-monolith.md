# ADR-0001 — Modüler monolit + ayrı worker

**Durum:** Önerildi · **Faz:** PHASE-00

## Bağlam
AIH hem SaaS hem self-hosted dağıtılacak. Self-hosted müşterilerde operasyon yükü düşük olmalı; SaaS tarafında
gönderim yükü API'den bağımsız ölçeklenmeli. Mikroservis için kanıtlanmış bir ihtiyaç henüz yok.

## Karar
- Tek deploy edilebilir **API uygulaması** (`apps/api`) + aynı kod tabanından **worker uygulaması** (`apps/worker`).
- Domain modülleri `modules/*` altında ayrı Maven modülleri: `identity`, `tenancy`, `providers`, `notifications`,
  `templates`, `credits`, `usage`, `billing`, `audit`. Ortak çekirdek `modules/common`.
- Modüller arası çağrı yalnızca modülün `api` paketindeki arayüzlerden yapılır; başka modülün `internal` paketine
  ve tablolarına doğrudan erişim yasak. ArchUnit testleri bu kuralı CI'da zorlar (PHASE-02 ile birlikte).
- Modüller arası asenkron iletişim transactional outbox → RabbitMQ (PHASE-05/06).
- Her modül kendi şemasında tablo sahibi: `iam`, `tenancy`, `provider`, `notification`, `credit`, `audit` …

## Sonuçlar
- Tek veritabanı, tek deployment; mikroservise bölmek gerekirse sınırlar hazır.
- Worker API'den bağımsız ölçeklenir, aynı jar'ı değil kendi Spring Boot uygulamasını çalıştırır.
- Modül sınırı ihlali derleme değil test zamanında yakalanır; ArchUnit kuralı zorunlu.

## Alternatifler
- **Mikroservisler:** operasyon maliyeti, dağıtık transaction ve self-hosted kurulum karmaşıklığı nedeniyle reddedildi.
- **Spring Modulith:** değerlendirmeye açık; PHASE-02'de modül sınır testleri için ArchUnit ile karşılaştırılacak.

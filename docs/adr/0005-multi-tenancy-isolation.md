# ADR-0005 — Multi-tenant izolasyon modeli

**Durum:** Önerildi · **Faz:** PHASE-00 (uygulama PHASE-02)

## Karar
- **Paylaşılan veritabanı, paylaşılan şema, satır bazlı izolasyon** (`tenant_id NOT NULL`, gerektiğinde `project_id`).
  İki savunma katmanı:
  1. Uygulama: `TenantContext` yalnızca doğrulanmış kimlikten (JWT claim / API key kaydı) doldurulur. Path/body'deki
     `tenantId` yetki kaynağı değildir; kimlikteki kapsamla eşleşmezse **404** döner (varlık sızdırmamak için).
  2. Veritabanı: PostgreSQL **Row Level Security**; her transaction başında `SET LOCAL app.tenant_id`. RLS politikası
     olmayan tenant tablosu migration testinde hata verir.
- Kaynak bazlı izolasyon matrisi:

| Katman | Mekanizma |
|---|---|
| API | Kimlikten tenant kapsamı, BOLA/IDOR negatif testleri |
| DB | `tenant_id` + RLS + bileşik indeks `(tenant_id, …)` |
| Queue | Mesaj başlığında `tenant_id`; consumer RLS bağlamını mesajdan değil iş kaydından kurar |
| Cache | Anahtarda tenant/project (ADR-0003) |
| Log/trace | `tenant_id` log alanı olabilir, **metric label olamaz** |
| Secret | `secret_ref` tenant'a bağlı; çözümleme tenant kontrolü yapar |
| Kota/kontör | Defter kayıtları tenant/project'e bağlı |
| UI | Tenant seçici yalnızca yetkili tenant'ları listeler |

- Kurumsal müşteri için **ayrı veritabanı** seçeneği PHASE-11'de değerlendirilir; kod tenant çözümlemesini soyut tutar.

## Sonuçlar
Her yeni endpoint ve tablo için çapraz-tenant negatif test zorunludur (CI kapısı).

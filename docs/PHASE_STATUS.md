# Faz Durumu

| Faz | Durum | Özet |
|---|---|---|
| PHASE-00 | Onay bekliyor | 12 ADR, lisans envanteri, tehdit modeli, risk listesi |
| PHASE-01 | Onay bekliyor | Backend/worker iskeleti, Docker Compose, UI paketi, admin kabuğu, marka, CI |
| PHASE-02 | Başlamadı | Identity, Tenant & Project |

## PHASE-01 özeti
- **Testler:** Maven 15/15 (common 8, api 6 Testcontainers, worker 1); UI Vitest 7/7; Next.js build + typecheck temiz.
- **Manuel doğrulama:** `make up-mail` → 4 servis healthy; API ve worker readiness `UP`; admin kabuğu TR/EN ve light/dark geçişi tarayıcıda kontrol edildi.
- **Lisans:** engelli lisans yok; inceleme gerektirenler (sharp-libvips LGPL-3.0, caniuse-lite CC-BY-4.0) envantere işlendi.
- **Açık riskler:** R-01 marka tescili, R-02 AGPL observability bileşenleri, R-09 public repo; CI ilk koşusu GitHub'da doğrulanmadı.
- **Sıradaki:** PHASE-02 (onay sonrası).

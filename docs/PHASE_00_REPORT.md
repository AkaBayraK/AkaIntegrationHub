# PHASE-00 — Discovery & License Gate Raporu

**Tarih:** 2026-10-15 · **Kod değişikliği:** yok (yalnızca dokümantasyon)

## Kapsam (onaya sunulan)
- Ürün: multi-tenant entegrasyon/bildirim platformu; ilk tüketiciler BuildingFlow, TraceFlow, AkaAI, üçüncü taraf Java/.NET.
- Dağıtım matrisi:

| Özellik | SaaS | Self-hosted |
|---|---|---|
| Kimlik | Keycloak (yönetilen) veya müşteri OIDC | Müşteri OIDC veya paketli Keycloak |
| Veri | Paylaşılan DB + RLS | Müşteriye ait tek DB |
| Provider credential | AIH secret store (şifreli) | Müşteri vault / şifreli DB |
| Observability | Merkezi, private network | Opsiyonel compose profili |
| Güncelleme | Sürekli | İmzalı sürüm + migration |

- Mevcut repolar (BuildingFlow/TraceFlow/AkaAI) bu fazda **incelenmedi**; erişim ve entegrasyon noktaları PHASE-13'te
  ayrı onayla analiz edilecek. Varsayım: her biri JWT/OIDC ile çalışan bir Next.js + Java/.NET uygulamasıdır.

## Teslimatlar
- ADR-0001 … ADR-0012 (`docs/adr`)
- Lisans envanteri ve bağımlılık politikası (`docs/licenses`)
- Tehdit modeli (`docs/security/THREAT_MODEL.md`)
- PHASE-01 uygulama planı (`docs/PHASE_01_PLAN.md`)

## Kabul kriterleri
| Kriter | Durum |
|---|---|
| Onaylı kapsam | Onaya sunuldu |
| ADR'ler | Tamam (Önerildi) |
| İlk SBOM / policy | Policy tamam; SBOM üretimi PHASE-01 CI'ında |
| Risk listesi | Aşağıda |

## Risk listesi
| # | Risk | Etki | Öneri |
|---|---|---|---|
| R-01 | "Aka Integration Hub" marka/alan adı tescil durumu bilinmiyor | Yüksek | Marka araştırması (hukuk) |
| R-02 | Grafana/Loki/Tempo AGPL-3.0 | Orta | Hukuk onayı; alternatif olarak yalnızca Prometheus + Collector |
| R-03 | RabbitMQ MPL-2.0 image'ının self-hosted pakette dağıtımı | Düşük | NOTICE + kaynak bağlantısı |
| R-04 | KVKK, İYS ve ülke bazlı SMS mevzuatı | Yüksek | Hukuk incelemesi PHASE-05 öncesi |
| R-05 | Provider'ların bakiye/top-up API'leri farklı ve belgesiz olabilir | Orta | Capability gating; desteklenmeyen işlem gizlenir |
| R-06 | Fallback'te çift gönderim ve çift ücretlendirme | Yüksek | Varsayılan fallback kapalı; `unknown` durumda manuel karar |
| R-07 | SMTP host'u üzerinden SSRF | Yüksek | T-04 önlemleri, PHASE-03 kabul kriteri |
| R-08 | Yerel makinede JDK 21 yok (JDK 25 var) | Düşük | `--release 21`; CI'da Temurin 21 |
| R-09 | GitHub reposu **public** | Orta | Ticari ürün için private yapılması önerilir |
| R-10 | Maliyet modeli için provider fiyatları toplanmadı | Orta | PHASE-07 öncesi provider bazlı fiyat tablosu |

## Maliyet modeli (taslak)
SaaS birim maliyeti = altyapı (DB, broker, cache, compute) + provider gönderim maliyeti (geçişli) + destek.
Fiyatlandırma: plan ücreti + kullanım (mesaj başı marj). Somut rakamlar provider sözleşmeleri olmadan **ölçülemiyor**.

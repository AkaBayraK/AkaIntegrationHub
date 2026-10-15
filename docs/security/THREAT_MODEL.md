# Tehdit Modeli (STRIDE, ilk sürüm)

## Varlıklar
Provider credential'ları (secret ref arkası), tenant verisi ve alıcı PII'si (telefon, e-posta, mesaj içeriği),
kontör defteri, API key'ler, audit kayıtları, şablonlar.

## Güven sınırları
1. İnternet → API (JWT / API key)
2. Host uygulama (BuildingFlow/TraceFlow/AkaAI) → gömülü UI → API
3. API/worker → dış sağlayıcılar (SMTP, SMS API) — **egress**
4. Sağlayıcı → webhook/callback uçları — **ingress, imzalı**
5. Uygulama → PostgreSQL / RabbitMQ / Valkey (özel ağ)
6. Uygulama → telemetri hattı (Collector)

## Tehditler ve önlemler

| # | STRIDE | Tehdit | Önlem | Faz |
|---|---|---|---|---|
| T-01 | E/I | Çapraz-tenant erişim (BOLA/IDOR) | Kimlikten tenant kapsamı, RLS, 404 politikası, negatif testler | 02 |
| T-02 | S | Çalınmış API key | Özet saklama, kapsam, rotasyon, IP allowlist (opsiyonel), anomali alarmı | 02 |
| T-03 | I | Secret'ın log/trace/yanıta sızması | Secret ref, maskeleme filtresi, log testleri, `toString` yasağı | 01→ |
| T-04 | T/E | SMTP host/webhook URL'si ile **SSRF** ve iç ağ taraması | DNS çözümleme sonrası IP doğrulama, özel/loopback/link-local/metadata bloğu, egress policy, DNS rebinding koruması | 03 |
| T-05 | S | Sahte provider callback | HMAC/imza doğrulama, zaman damgası penceresi, replay önleme (dedup) | 06 |
| T-06 | R | Kontör manipülasyonu inkârı | Append-only defter, dört-göz onayı, audit | 07 |
| T-07 | D | Toplu gönderim ile kaynak tüketme | Rate limit, kota, kuyruk sınırları, backpressure | 06/07 |
| T-08 | T | Şablon enjeksiyonu (SSTI/XSS) | Mantıksız şablon motoru, değişken şema doğrulaması, HTML escape | 05 |
| T-09 | I | PII'nin metrik label'ına girmesi | Label allowlist, kardinalite testi | 10 |
| T-10 | E | Gömülü UI üzerinden host token'ının sızması | Token yalnızca bellek, CSP, aynı-origin API proxy seçeneği | 08 |
| T-11 | T | Tedarik zinciri (bağımlılık/image) | Sürüm pin, SBOM, lisans/CVE kapısı, imzalı release | 01/14 |
| T-12 | I | Mailpit'e gerçek e-posta düşmesi | Mailpit yalnız `dev-mail` profili, prod'da fail-closed guard | 04 |
| T-13 | E | Rastgele adapter kodu yükleme | Yalnızca derlenmiş, imzalı adapter'lar; runtime plugin yükleme yok | 03 |

## Açık noktalar
KVKK/GDPR saklama süreleri, ülke bazlı SMS mevzuatı ve ticari ileti onayı (İYS) hukuk incelemesi gerektirir;
bu doküman uyumluluk garantisi vermez.

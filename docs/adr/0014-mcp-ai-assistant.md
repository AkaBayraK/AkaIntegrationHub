# ADR-0014 — MCP tabanlı AI yapılandırma asistanı

**Durum:** Önerildi · **Faz:** PHASE-17 · **Bağımlı:** ADR-0005, ADR-0006, ADR-0007, ADR-0013

## Bağlam
Ürün sahibi, SMTP, SMS ve benzeri bağlantı tanımlarının yapay zekâ ile, Model Context Protocol (MCP) üzerinden
yapılabilmesini istiyor. Örnek: "Tenant X için Microsoft 365 SMTP hesabı ekle, bağlantıyı test et, varsayılan yap."

## Karar
1. **MCP bağlantıyı kurmaz.** SMTP/SMS/webhook/Kafka gibi dış sistemlere bağlantıyı yalnızca PHASE-03 provider adapter'ları kurar.
   MCP sunucusu, yapay zekânın **AIH'nin kendi API'sini** çağırmasını sağlayan ince bir katmandır.
2. MCP sunucusu `apps/mcp` altında, resmi MCP Python SDK ile yazılır ve REST API ile **aynı servis katmanını** kullanır.
   Doğrulama, yetki, tenant izolasyonu, idempotency ve audit iki kez yazılmaz.
3. Taşıma: uzak istemciler için Streamable HTTP; yetkilendirme MCP yetkilendirme spesifikasyonuna uygun OAuth 2.1
   (Keycloak/OIDC, ADR-0006). Token tenant ve proje kapsamlıdır; tenant id istemciden alınmaz, token'dan türetilir.
4. İlk araç seti (provider türünden bağımsız, capability tabanlı):

| Araç | Tür | Not |
|---|---|---|
| `list_provider_types` / `describe_provider_capabilities` | Okuma | Hangi alanların, auth yöntemlerinin desteklendiği |
| `list_provider_accounts` / `get_provider_account` | Okuma | Secret değerleri hiç dönmez; yalnızca `secret_ref` ve maske |
| `draft_provider_account` | Yazma (taslak) | Hesap **taslak** durumunda oluşur, aktif olmaz |
| `test_provider_connection` | Eylem | DNS/TCP/TLS/AUTH adımları; gerçek gönderim yapmaz |
| `request_activation` | Eylem | Taslağı aktifleştirme isteği; insan onayı gerekir |
| `make_default` / `disable_account` | Yazma | İnsan onayı gerekir |

5. **Secret'lar yapay zekâya gitmez.** Şifre, API key ve OAuth token'ları kullanıcı UI'daki güvenli formdan veya OAuth
   yönlendirmesiyle girer, vault/encrypted store'a yazılır. MCP araçları yalnızca `secret_ref` alır ve döndürür;
   prompt, araç argümanı, log veya trace'e secret düşmez.
6. **İnsan onayı:** Kalıcı etkili yazma işlemleri (aktifleştirme, varsayılan yapma, pasifleştirme, test e-postası gönderme)
   admin UI'da onaylanana kadar uygulanmaz. Onay ekranı değişikliğin diff'ini gösterir.
7. **Audit:** her araç çağrısı `actor=user`, `via=mcp`, `agent_client_id`, araç adı ve sonuçla audit'e yazılır.

## Kapsam sınırları
- **SMTP, SMS, e-posta API, WhatsApp, push, webhook:** tenant provider hesapları → MCP ile tanımlanabilir.
- **Kafka:** mevcut tasarımda yok. Müşterinin Kafka'sına olay yayını gerekirse PHASE-12'de bir "hedef connector" olarak
  eklenir (istemci: confluent-kafka-python, Apache-2.0; librdkafka BSD-2-Clause) ve sonra MCP'ye açılır.
  AIH'nin kendi kalıcı kuyruğu RabbitMQ olarak kalır (ADR-0003).
- **Valkey/Redis ve RabbitMQ:** AIH'nin kendi altyapısıdır; deployment konfigürasyonuyla kurulur, tenant'lar MCP ile
  değiştiremez. Redis Server lisans kısıtı ADR-0003'te geçerlidir.

## Güvenlik
- **SSRF:** host/port alanları sunucu tarafında allowlist ve özel ağ kısıtıyla doğrulanır (`docs/design/SMTP_ADMIN_UI_DESIGN.md`
  ve `docs/design/BLACKBOX_EXPORTER_DESIGN.md` kuralları). Yapay zekânın önerdiği host da aynı kontrolden geçer.
- **Prompt injection:** araç çıktıları (sağlayıcı hata mesajları dahil) maskeli ve kısaltılmış döner; araçlar
  rol ve tenant kapsamını aşan işlem yapamaz; yıkıcı araç yoktur (silme yok, yalnızca pasifleştirme).
- Araç başına rate limit, kısa ömürlü token, deny-by-default. Viewer rolü yalnızca okuma araçlarını görür.
- Cross-tenant negatif testler MCP araçları için de zorunludur (BOLA/IDOR).

## Sonuçlar
- AI ile tanımlama, UI ile tanımlamayla aynı kuralları paylaşır; ayrı bir "AI arka kapısı" oluşmaz.
- PHASE-17, PHASE-02 (kimlik/RBAC) ve PHASE-03/04 (provider registry ve kanallar) tamamlanmadan başlayamaz.
- LLM sağlayıcısı seçimi (barındırılan model veya self-hosted) ayrı ADR'dir; MCP sunucusu modelden bağımsızdır.

## Alternatifler
- **AI'nın doğrudan veritabanına/sağlayıcıya bağlanması:** yetki ve audit atlanır; reddedildi.
- **AI'ya secret girdirmek:** secret'ın model geçmişine ve loglara sızma riski; reddedildi.

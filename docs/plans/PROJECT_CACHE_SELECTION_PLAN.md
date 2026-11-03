# Proje Bazlı Cache Seçimi ve Ayar Dağıtımı — Plan

Durum: **Planlandı** · Faz: PHASE-02 (projeler) + PHASE-09 (SDK) · İlgili: `docs/design/CACHE_VALKEY_DESIGN.md`

## Amaç

BuildingFlow, TraceFlow ve sonraki uygulamalar Hub'da tanımlı cache hesaplarından birini (Valkey ya da lisansı
beyan edilmiş Redis) seçer ve kod değiştirmeden kullanır. Cache trafiği Hub'dan geçmez; Hub yalnız bağlantı
ayarını güvenli şekilde dağıtır.

## Bugün hazır olanlar

- Cache hesapları: Valkey ve müşteri Redis'i, ACL/şifre (şifreli), TLS, veritabanı, anahtar ön eki.
- Redis için lisans beyanı (tür, sahip, sözleşme no, bitiş, ticari anahtar şifreli, onaylayan + audit).
- `project_id` sütunu ve **tenant + proje + ortam başına tek varsayılan** kısıtı (`uq_cache_single_default`).
- Bağlantı testi ve sunucu özeti.

## Yapılacaklar

### 1. Projeler (PHASE-02)
- `tenancy.projects` tablosu (tenant, slug, ad, durum) ve proje yönetimi API/ekranı.
- Cache formunda **Proje** seçimi; hesap kartında proje rozeti. Projesi olmayan hesap "tüm projeler" varsayılanıdır.
- Çözümleme sırası: proje + ortam varsayılanı → tenant + ortam varsayılanı → hata (`AIH-CACHE-020`).

### 2. Servis kimliği
- Her uygulama için Keycloak'ta client-credentials istemcisi (`buildingflow-backend`, `traceflow-backend`) ve
  `cache-config:read` izni. Tarayıcıya hiçbir zaman cache şifresi gitmez.

### 3. Ayar dağıtım ucu
`GET /v1/projects/{projectId}/cache-config?environment=production` →

```json
{
  "provider": "valkey",
  "host": "cache.internal", "port": 6379, "tls": true, "database": 0,
  "keyPrefix": "buildingflow:",
  "username": "buildingflow-app",
  "credential": { "password": "…", "expiresAt": "2026-11-03T12:00:00Z" },
  "configVersion": 7
}
```

- Yalnız servis kimliğiyle ve kendi projesi için çağrılabilir (IDOR/BOLA negatif testleri zorunlu).
- Yanıt `Cache-Control: no-store`; şifre loglanmaz, audit'e yalnız "config okundu" yazılır.
- Redis hesabında lisans **süresi dolmuşsa** ayar verilmez (`AIH-CACHE-021`), bitişe 30 gün kala yanıtta uyarı alanı.
- `configVersion` değişince uygulama yeniden bağlanır (Hub, RabbitMQ'ya `cache-config.changed` olayı yayınlar).

### 4. Uygulama tarafı (SDK, PHASE-09)
- Java (Spring Boot): `aka-integration-spring-boot-starter` açılışta ayarı çeker ve `LettuceConnectionFactory`
  oluşturur; anahtar ön eki `RedisCacheConfiguration.prefixCacheNameWith` ile uygulanır.
- .NET: `Aka.Integration.Cache` paketi `ConnectionMultiplexer` yapılandırmasını üretir.
- Valkey 8 ve Redis 7.2+ aynı RESP protokolünü konuştuğu için uygulama kodu değişmez. Redis 8'e özel modüller
  (sorgu motoru, JSON vb.) kullanılacaksa proje Redis hesabı seçmelidir; Hub bunu hesap kartında belirtir.

### 5. Ekranlar
- Proje detayında "Cache" kartı: seçili hesap, sağlayıcı (Valkey/Redis), lisans durumu, son test, değiştir düğmesi.
- Değiştirme onay ister; eski ve yeni hesap audit'e yazılır.

## Kabul kriterleri

- İki proje aynı tenant'ta farklı cache hesabı kullanabilir; biri diğerinin ayarını okuyamaz (negatif test).
- Lisansı dolmuş Redis hesabı hiçbir projeye dağıtılmaz.
- Ayar değişince bağlı uygulama 60 sn içinde yeni hesaba geçer.
- Cache şifresi log, trace, audit veya tarayıcı yanıtında görünmez (Trivy secret taraması + test).

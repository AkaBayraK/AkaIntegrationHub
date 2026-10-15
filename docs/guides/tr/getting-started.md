# Başlangıç (Lokal geliştirme)

1. `.env.example` dosyasını `.env` olarak kopyalayın (`make up` bunu otomatik yapar) ve parolaları değiştirin.
2. `make up` — PostgreSQL 17.6, Valkey 8.1.4 ve RabbitMQ 4.1.4 sağlıklı duruma gelene kadar bekler.
3. `make api` — API ilk açılışta Flyway ile `platform` şemasını oluşturur.
4. Hazır olma kontrolü: `curl localhost:28081/actuator/health/readiness` → `{"status":"UP"}`.
   Readiness; veritabanı, Valkey ve RabbitMQ'nun hepsine erişilebildiğinde `UP` olur.
5. `curl -H 'X-Correlation-Id: deneme-0001' localhost:28080/v1/system/info` — yanıt başlığında aynı korelasyon kimliği döner.
6. Yönetim konsolu: `npm install && npm run build && make web` → http://localhost:28030. Geliştirme kabuğunda
   "Giriş yap" gerçek kimlik doğrulama yapmaz (PHASE-02).

## Sorun giderme
- **Port dolu:** `.env` içindeki `AIH_*_HOST_PORT` değerlerini değiştirin; uygulama tarafında aynı değerleri
  `AIH_DB_URL`, `AIH_VALKEY_PORT`, `AIH_RABBITMQ_PORT` ile verin.
- **Testler Docker bulamıyor:** Testcontainers için Docker Desktop çalışıyor olmalı.

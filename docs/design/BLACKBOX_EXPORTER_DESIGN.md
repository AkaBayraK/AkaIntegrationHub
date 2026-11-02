# AKA INTEGRATION HUB — BLACKBOX EXPORTER DESIGN (PHASE-10.10 / V5)

## Amaç
Prometheus Blackbox Exporter ile yalnızca önceden yetkilendirilmiş servis uç noktalarının erişilebilirliğini ve ağ davranışını dışarıdan kontrol etmek. OTel Collector'ın yerine geçmez; iş mantığı metriklerini ve SMS teslimat sonuçlarını ölçmez.

## Entegrasyon
Prometheus -> Blackbox Exporter `/probe?module=...&target=...` -> allowlist kapsamındaki HTTP(S)/TCP/DNS hedefi -> `probe_success`, `probe_duration_seconds`, `probe_http_status_code`, `probe_ssl_earliest_cert_expiry` -> Prometheus kuralları -> Alertmanager -> yetkili bildirim kanalı. Grafana dashboard'u yalnızca erişim yetkisiyle sunulur.

## Uygulama sırası
1. Mevcut Compose, Prometheus jobs, network ve alarm yapılandırmasını analiz et; kod değiştirme ve onay bekle.
2. `blackbox-exporter` servisini yalnızca opsiyonel `observability` profiline eklemeyi planla; portu internete yayınlama, minimum container yetkileri ve resource limitleri uygula.
3. `blackbox.yml` için kontrollü HTTP(S), TCP, DNS modüllerini tanımla; ICMP sadece yetki ve ortam desteği varsa. TLS doğrulamasını kapatma.
4. Prometheus `scrape_configs` içinde sabit hedef listesi ve relabeling kullan. Son kullanıcı URL'sini `/probe` için doğrudan kullanma.
5. Grafana'da Service Health, latency, DNS, TLS expiry dashboard'larını provisioning ile sürümle.
6. Alertmanager: probe failure (kısa kesintilerde yanlış alarmı azaltacak `for`), sertifika son kullanım eşiği, süre aşımı, DNS sorunları. Bakım penceresi ve alarm tekrarını yönet.
7. Audit: hedef değişikliklerini SystemAdmin onayı ve kayıtlarıyla yönet; SaaS tenant izolasyonu ve yetkilendirme testleri.
8. Mock HTTP/TCP/DNS endpoint testleri, hatalı sertifika, timeout, exporter-down, false positive, auth ve SSRF güvenlik testlerini tamamla; raporla ve onay bekle.

## Güvenlik sınırları
- Target allowlist, egress network policy, DNS rebinding koruması; loopback, link-local, metadata servisleri ve izin verilmeyen özel IP aralıklarına probe yapılmaz.
- Yetkisiz tenantlar exporter'a doğrudan erişemez. Sistem içi hedefler yalnızca açıkça tanımlanmış yönetim kapsamındadır.
- Credential/token/query-string içeren URL'leri log, label veya dashboard'da gösterme. Sağlayıcıların rate limit ve kullanım koşullarını gözet.
- SMS sağlayıcısı probe'u sadece ulaşılabilirliği gösterir; SMS teslimi için provider callback, delivery status ve iş metrikleri kullanılır.
- SMTP için TCP bağlantısı servis erişimini gösterir; e-posta teslimini garanti etmez.
- İşlem akışı monitoring devre dışıyken de çalışır. Yeni bağımlılık ve lisanslar sürüm bazında incelenir.

## Kabul kriterleri
- Bilinen test endpoint'i açıkken `probe_success=1`, kapalıyken `0`.
- Sertifika bitiş uyarısı örnek testle doğrulanır.
- Grafana servis sağlık ekranı ve alarm çalışır; alarm döngüsü oluşmaz.
- Yetkisiz adres, tenant veya metadata endpoint'i probe edilemez.
- TraceFlow'un mevcut SMS ekranı değişmez; Hub SMS Gateway geçişi ayrı PHASE-13 kapsamında isteğe bağlı yapılır.

## Claude Code / Codex çalışma disiplini
Yalnızca PHASE-10.10 analizi ile başla; mevcut dosyaları ezme. Konsola `[AKA-HUB][PHASE-10.10][STEP-x][STATUS]` biçiminde Türkçe yaz. Etki analizi, dosya listesi, test planı ve riskleri bildirip onay bekle.

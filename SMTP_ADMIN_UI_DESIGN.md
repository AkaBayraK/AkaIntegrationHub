# SMTP Yönetimi — UI/UX Şartnamesi (V6)

## Temel karar
Aka Integration Hub, SaaS ve self-hosted kullanımda her tenant için birden fazla gerçek SMTP hesabı ve test ortamında Mailpit destekler. TraceFlow/BuildingFlow içindeki mevcut SMS/e-posta ekranları korunur; ortak API ve gömülebilir React bileşenleriyle bağlanır. Bu belge tasarım/geliştirme şartnamesidir; çalışan ekran değildir.

## Ekran 1: SMTP Hesapları (`/admin/email/providers`)
- Üstte tenant/proje seçimi (RBAC kapsamından); arama, sağlayıcı, ortam, durum filtreleri.
- Tablo: görünen ad, provider, maskelenmiş host, port, gönderici adresi, varsayılan/yedek, son bağlantı testi, son başarılı gönderim, durum.
- İşlemler: Yeni hesap, Düzenle, Bağlantı Testi, Test E-postası, Varsayılan Yap, Yedeğe Al, Pasifleştir, Audit.
- İzinler: PlatformAdmin yetkili tenantlarda; TenantAdmin yalnızca kendi tenantında; Viewer salt-okunur ve credential bilgileri görünmez.
- Empty/loading/error/unauthorized durumları, mobil responsive ve erişilebilirlik; TR/EN; confirmation dialog ve toast.

## Ekran 2: SMTP Hesap Tanımı (`/admin/email/providers/new`, `/:id/edit`)
- Alanlar: tenant, proje (opsiyonel), hesap adı, sağlayıcı tipi (Custom SMTP, Microsoft 365, Google Workspace, Amazon SES SMTP, Mailpit-test), host, port, TLS modu (STARTTLS/implicit TLS), sender address/name, reply-to, auth yöntemi (OAuth2 veya SMTP AUTH sağlayıcıya göre), username, secret reference, timeout, rate limit, aktif, varsayılan, öncelik, test/production ortamı.
- Şifre ve OAuth2 tokenı asla geri okunmaz, yalnızca rotate/revoke. Secret değerleri vault/encrypted store'a yazılır; UI maskeler; audit secret içeriğini saklamaz.
- Port/TLS uyumu, e-posta doğrulama, DNS/TLS sertifika doğrulama; allowlist ve SSRF koruması. Production'da TLS zorunlu; şifresiz mod sadece izole test ortamında.
- Test bağlantısı gerçek e-posta göndermez; ayrı Test E-postası aksiyonu onay ve güvenli test alıcısı ister. Sonuçlar adım bazlı (DNS/TCP/TLS/AUTH/SMTP kabulü) ve hassas veri maskelenmiş olarak gösterilir.
- Kaydetmeden önce doğrulama; optimistic locking/version; tenant'a göre tek varsayılan; geçmişteki gönderimlerin sağlayıcı kimliği korunur.

## Ekran 3: E-posta Gönderim Geçmişi (`/admin/email/deliveries`)
- Filtre: tarih, tenant, proje, sağlayıcı, durum, correlationId, template, kanal.
- Durumlar: queued, sending, accepted_by_smtp, failed, retry_scheduled, cancelled; SMTP kabulü alıcıya teslim edildi demek değildir. Destekleniyorsa teslim/bounce webhook olayları ayrı gösterilir.
- Satır detayında zaman çizelgesi, maskeleme uygulanmış hata, deneme sayısı, süre, SMTP response sınıfı, trace bağlantısı, idempotency key. Yetkisiz kullanıcı içerik/ek göremez.
- Retry/replay yalnızca güvenli idempotency kurallarıyla; CSV export rol ve veri minimizasyonuna tabi.

## Ekran 4: Test Gelen Kutusu — Mailpit (`/admin/email/test-inbox`)
- Yalnızca dev/test ortamlarında etkin; tenant/project test context seçimi, inbox listesi, HTML/plain-text preview, MIME/ek bilgileri, test sonuçları.
- Mailpit web UI'sini doğrudan herkese açma; tercihen backend proxy/adapter + rol kontrollü kısıtlı API; gerekiyorsa sadece geliştirici VPN erişimi.
- Production'da test inbox gizli/devre dışı. Gerçek kullanıcı PII'si ve gerçek production e-postası Mailpit'e yönlendirilmez.

## Ortak UX
- Masaüstü sol menü: İletişim > E-posta > SMTP Hesapları / Gönderim Geçmişi / Şablonlar / Test Gelen Kutusu (test only).
- Üst bilgi, breadcrumb, boş durumlar, loading skeleton, klavye erişimi, kontrast, TR/EN ve light/dark.
- UI paketi `@aka/integration-ui` bağımsız Next.js admin ve host uygulamalara gömülebilir; host'un kimlik, tema, dil ve tenant context'ini kullanır.

## Kabul kriterleri
1. İki tenant'ın SMTP hesapları API/UI/DB düzeyinde ayrıdır; cross-tenant erişim testleri başarısız olmalı.
2. TenantAdmin birden fazla hesap oluşturup varsayılan/yedek değiştirebilir; audit kayıtları vardır.
3. OAuth2 ve SMTP AUTH yalnızca sağlayıcı yetenekleriyle uyumlu seçilir; secret asla okunabilir dönmez.
4. Test bağlantısı ile test e-postası ayrı aksiyonlardır; Mailpit test mesajını yakalar.
5. Üretim profilinde Mailpit'e otomatik yönlendirme yapılamaz; gerçek SMTP ayrı profil ile seçilir.
6. Mevcut TraceFlow/BuildingFlow ekranları değiştirilmeden API/SDK ile entegrasyon testi yapılır.

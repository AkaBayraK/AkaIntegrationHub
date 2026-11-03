# SMS Entegrasyonu — Analiz ve BuildingFlow/TraceFlow Geçiş Planı

Durum: **Hub tarafı uygulandı (2026-11-03)** · Geçiş: BuildingFlow ve TraceFlow'da ayrı iş · İlgili: PHASE-04, PHASE-05

## 1. Mevcut durum (incelenen kod)

| Konu | BuildingFlow (.NET) | TraceFlow (Java/Spring) |
|---|---|---|
| Hesap | `SmsAccount` — mülk (property) başına tek hesap | `SmsAccount` — şirket başına tek hesap |
| Sağlayıcı | `SmsProvider { MOCK }`; ayrıca platform OTP için `NetgsmPhoneOtpSender` (XML, `/sms/send/otp`) | `SmsProviderType { MOCK, NETGSM, ILETI_MERKEZI, VERIMOR, TURKCELL }`, yalnız `MockSmsProvider` uygulanmış |
| Kimlik bilgisi | Kullanıcı adı + şifreli sır + HTTPS API URL | Kullanıcı adı + AES-GCM şifreli sır + API URL |
| Kontör | `CreditBalance`, `LowCreditThreshold`, `SmsCreditTransaction` (LOAD/CONSUME/REFUND/ADJUST) | Aynı model; bakiye atomik SQL ile düşülür |
| Mesaj | Kuyruk + dispatcher (`FOR UPDATE SKIP LOCKED`), maskeli numara/metin, şifreli payload | 3 adım: rezervasyon → sağlayıcı (tx dışı) → sonuç/iade; belirsiz sonuç `UNKNOWN` |
| Amaç / uyum | `SmsCategory`, yasal dayanak, İYS ticari onay, opt-out alt bilgisi (`ISmsPolicyResolver` — "ileride Hub sağlayabilir") | `SmsPurpose { OTP, TRANSACTIONAL, OPERATIONAL, SECURITY, MARKETING }` |
| Metin | Şablon (`SmsTemplate`) + tip kataloğu, hassas parametre maskeleme | Şablon + `SmsType` (parametre listesi, hassas parametreler) |
| Kurallar | TR cep E.164, GSM-7/UCS-2 parça hesabı, başlık 3-11 | Aynı (`PhoneNumbers`, `SmsSegments`) |

İki projede de **aynı sorunlar** var: her biri kendi kontörünü, sağlayıcı bilgisini ve gönderim kaydını ayrı tutuyor;
gerçek operatör adaptörü (Netgsm genel gönderim) iki tarafta da yok.

## 2. Hub'da ne yapıldı

- **SMS hesapları** (`/v1/tenants/{id}/sms-accounts`): sağlayıcı, gönderici başlığı, kullanıcı kodu, şifreli API şifresi,
  ortam, varsayılan hesap (tenant + proje + ortam başına tek), düşük kontör eşiği, yönetim arayüzü adresi.
- **Sağlayıcılar**: `mock_test` (yalnız dev/test; operatöre gitmez) ve **Netgsm** (XML `/sms/send/xml`, sabit adres → SSRF
  yok, 10 sn zaman aşımı, yönlendirme yok, ham yanıt saklanmaz). İleti Merkezi, Verimor, Turkcell "yakında" olarak listelenir.
- **Kontör Hub'da**: yükleme/düzeltme (`/credits`), her hareket defterde (`balance_after` ile); bakiye tek atomik SQL ile
  değişir, eksiye düşemez.
- **Gönderim API'si** `POST /v1/tenants/{id}/sms/messages` (`Idempotency-Key` zorunlu):
  1. Doğrulama (TR cep, ≤ 10 parça, ticari iletide `consentReference` zorunlu) + kontör ayırma + `queued` kayıt.
  2. Sağlayıcı çağrısı transaction dışında.
  3. `sent`; kesin hatada `failed` + **kontör iadesi**; belirsizde `unknown` (iade yok, mutabakat bekler).
- **Gizlilik**: numara yalnız maskeli (`+90532*****67`) ve tenant tuzlu özetle saklanır; mesaj metni saklanmaz.
- **Test SMS'i**: test sağlayıcısında her numaraya, gerçek sağlayıcıda yalnız `AIH_SMS_TEST_RECIPIENT_ALLOWLIST` numaralarına.
- **Ekran**: SMS Hesapları — kontör bakiyesi ve uyarısı, kontör yükleme, test SMS'i, son gönderimler, kontör defteri.
- İzinler: `sms-account:read|write|test`, `sms-credit:manage`, `sms:send`, `sms-message:read` (Viewer yalnız okur).

> Netgsm yanıt kodu eşlemesi (00/01/02 başarı; 20, 30, 40, 50/51, 70, 85 kesin hata) Netgsm XML API belgesine göre
> yazıldı; **canlı bir Netgsm hesabıyla doğrulanmadı**. İlk gerçek testten önce kod eşlemesi kontrol edilmelidir.

## 3. Uygulamaların Hub'a geçişi

Uygulamalarda **şablon, tip kataloğu ve uyum kararı (KVKK/İYS politika çözücüsü) kalır**; Hub'a yalnız gönderim gider.
Böylece BuildingFlow'un `ISmsPolicyResolver` ve TraceFlow'un `SmsType` yapıları değişmez.

| Adım | BuildingFlow | TraceFlow |
|---|---|---|
| 1. Hub istemcisi | `ISmsProvider` için `HubSmsProvider` (HttpClient) | `SmsProvider` için `HubSmsProvider` (`@Component`, `SmsProviderType.HUB`) |
| 2. Kimlik | Keycloak client-credentials (`buildingflow-backend`, `sms:send`) | Aynı (`traceflow-backend`) |
| 3. Eşleme | `SmsPurpose`/`SmsCategory` → Hub `purpose`; İYS onay kimliği → `consentReference` | `SmsPurpose` → Hub `purpose` |
| 4. Idempotency | `sms_messages.id` → `Idempotency-Key` | `sms_message.id` veya outbox id → `Idempotency-Key` |
| 5. Sonuç | Hub `sent/failed/unknown` → yerel durum; `unknown` mutabakat kuyruğuna | Aynı (`UNKNOWN` zaten var) |
| 6. Kontör | Yerel bakiye salt okunur olur; Hub bakiyesi gösterilir, yükleme Hub'dan | Aynı |
| 7. Geçiş | Özellik bayrağı: `Sms:Transport = Local | Hub`; önce test ortamı | `traceflow.sms.transport=LOCAL|HUB` |

Sözleşme örneği:

```http
POST /v1/tenants/{tenantId}/sms/messages
Idempotency-Key: bf-sms-6f1c…
Content-Type: application/json

{
  "environment": "production",
  "phone": "05321234567",
  "body": "Sayın sakinimiz, Kasım aidatınızın son ödeme günü 10.11.2026'dır.",
  "purpose": "operational",
  "typeCode": "DUES_NOTIFICATION",
  "reference": { "type": "dues", "id": "INV-2026-1104" }
}
```

## 4. Sonraki işler

- Teslim raporu (DLR) callback'i ve imza doğrulaması (PHASE-06) → `delivered` durumu.
- `unknown` kayıtlar için sağlayıcı sorgusuyla mutabakat işi (worker).
- İleti Merkezi / Verimor / Turkcell adaptörleri (aynı `SmsGateway` sözleşmesi).
- Proje bazlı varsayılan hesap ve servis kimliği (bkz. `PROJECT_CACHE_SELECTION_PLAN.md` ile aynı yaklaşım).
- Kontör düşük uyarısının e-posta/bildirim olarak gönderilmesi (PHASE-05).

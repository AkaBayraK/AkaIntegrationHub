# BuildingFlow ve TraceFlow'dan Hub ekranını açmak (PHASE-13)

Hub yönetim ekranı host uygulamaya gömülmez; host menüsündeki **Entegrasyonlar** bağlantısı Hub admin web'i açar.
Kimlik, host ile aynı Keycloak realm'inden SSO ile gelir (kullanıcı kararı 02.11.2026: "Menü linki + ortak Keycloak SSO").

```text
Host menüsü ─► <HUB>/admin/email/providers?idp=<id>&host=<ad>&locale=tr|en&theme=light|dark&return=<host sayfası>
                    │
                    └─► keycloak-js (aih-admin-web, PKCE S256) ─► aynı realm, oturum açık → giriş ekranı yok
                                        │
                                        └─► AIH API: issuer kayıtlı mı? → tenant + rol eşlemesi (claim'den değil, kayıttan)
```

## 1. Keycloak

Her realm'de public client `aih-admin-web`: standard flow, PKCE S256, password grant kapalı,
redirect `http://localhost:28030/*`, web origin `http://localhost:28030`.
Realm dosyalarına eklendi (BuildingFlow `deploy/keycloak/realm-buildingflow.json`,
TraceFlow `infra/keycloak/realm-export.json`). Çalışan Keycloak'a admin konsolundan aynı ayarlarla ekleyin.

## 2. Hub tenant kayıtları

```bash
uv run aih-api register-tenant --slug buildingflow --name "BuildingFlow" \
  --issuer http://localhost:8080/realms/buildingflow --client-id aih-admin-web \
  --tenant-admin-roles SUPER_ADMIN,SITE_ADMIN --viewer-roles MANAGER

uv run aih-api register-tenant --slug traceflow --name "TraceFlow" \
  --issuer http://localhost:8081/realms/traceflow-realm --client-id aih-admin-web \
  --tenant-admin-roles SYSTEM_ADMIN --viewer-roles CENTER
```

API'nin CORS listesine admin web origin'i (`AIH_CORS_ORIGINS=http://localhost:28030`) eklenmiş olmalıdır.

## 3. Hub admin web (`apps/admin-web/.env`)

`NEXT_PUBLIC_AIH_IDPS` iki realm'i, `NEXT_PUBLIC_AIH_HOST_RETURN_ORIGINS` host origin'lerini
(`http://localhost:3003` BuildingFlow, `http://localhost:3000` TraceFlow) içerir. Listede olmayan `return` adresi yok sayılır.

## 4. Host uygulamalar

| Host | Menü | Yapılandırma | Görünür roller |
|---|---|---|---|
| BuildingFlow | Yönetim > Entegrasyonlar (`/integrations`) | `NEXT_PUBLIC_AKA_INTEGRATION_HUB_URL` | SUPER_ADMIN, SITE_ADMIN, MANAGER |
| TraceFlow | Ayarlar > Entegrasyonlar (`/integrations`) | `VITE_AKA_INTEGRATION_HUB_URL` | SYSTEM_ADMIN, CENTER |

Menü görünürlüğü yalnız kullanıcı deneyimidir; yetkiyi Hub API her istekte yeniden doğrular.

## Güvenlik notları

- URL'de token, OIDC `code`/`state` veya kişisel veri taşınmaz; host `return` adresinden sorgu ve fragment'i atar.
- SMTP sırrı host uygulamalara hiç gelmez; host backend'leri Hub'a çağrı yapmaz.
- `X-AIH-Dev-User` yalnız `local`/`test` ortamında ve `AIH_AUTH_DEV_MODE=true` iken çalışır.

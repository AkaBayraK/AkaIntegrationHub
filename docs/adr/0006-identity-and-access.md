# ADR-0006 — Kimlik, RBAC ve API key

**Durum:** Önerildi · **Faz:** PHASE-00 (uygulama PHASE-02)

## Karar
- API bir **OAuth2 Resource Server**'dır; JWT'yi (OIDC) doğrular. Keycloak varsayılan ve opsiyonel IdP'dir; herhangi
  bir OIDC uyumlu IdP (Entra ID, Auth0, host uygulamanın IdP'si) yapılandırmayla bağlanabilir.
- Roller: `PlatformAdmin` (SaaS operatörü, tenant dışı), `TenantAdmin`, `ProjectAdmin`, `Operator`, `Viewer`,
  `ServiceAccount`. Rol atamaları AIH veritabanında tutulur (IdP'den bağımsız, tenant/project kapsamlı).
- İzinler `resource:action` biçiminde (`smtp-account:write`, `notification:send` …); rol → izin eşlemesi kodda sabit,
  kapsam kontrolü `@PreAuthorize` + kapsam değerlendiricisi ile.
- **API key:** makineden makineye. Biçim `aih_{env}_{keyId}_{secret}`; DB'de yalnızca `keyId` ve secret'ın
  Argon2id/SHA-256-HMAC özeti. Bir anahtar tek tenant + opsiyonel proje + izin kümesine bağlıdır. Rotasyon için
  aynı anda iki aktif anahtar; son kullanım zamanı ve süre sonu tutulur.
- Deny-by-default; yetki servisi hatasında fail-closed.
- PlatformAdmin bir tenant verisine erişirse audit kaydı zorunlu ("break-glass").

## Alternatifler
Tamamen Keycloak'a gömülü yetkilendirme (Authorization Services): self-hosted'da IdP bağımsızlığını bozduğu için reddedildi.

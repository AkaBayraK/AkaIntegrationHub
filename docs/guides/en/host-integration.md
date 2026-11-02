# Opening the Hub screens from BuildingFlow and TraceFlow (PHASE-13)

The Hub admin UI is not embedded. An **Integrations** menu item in each host opens the Hub admin web with
`?idp=<id>&host=<name>&locale=tr|en&theme=light|dark&return=<host page>`. Sign-in is SSO against the host's own
Keycloak realm through the public PKCE client `aih-admin-web`; the Hub API maps issuer → tenant and IdP roles → Hub roles
from its own registry, never from token claims.

- Keycloak: add `aih-admin-web` (public, standard flow, PKCE S256, redirect `http://localhost:28030/*`) to each realm.
- Hub: `aih-api register-tenant` for `buildingflow` (SUPER_ADMIN,SITE_ADMIN → TenantAdmin; MANAGER → Viewer) and
  `traceflow` (SYSTEM_ADMIN → TenantAdmin; CENTER → Viewer). See the Turkish guide for the exact commands.
- Admin web: `NEXT_PUBLIC_AIH_IDPS` and `NEXT_PUBLIC_AIH_HOST_RETURN_ORIGINS` (`http://localhost:3003`, `http://localhost:3000`).
- Hosts: BuildingFlow `NEXT_PUBLIC_AKA_INTEGRATION_HUB_URL`, TraceFlow `VITE_AKA_INTEGRATION_HUB_URL`.

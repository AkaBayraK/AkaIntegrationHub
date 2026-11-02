/** Tarayıcıya açık (NEXT_PUBLIC_*) yapılandırma. Burada asla sır tutulmaz. */

export interface IdentityProviderConfig {
  id: string;
  label: string;
  /** OIDC issuer, ör. http://localhost:8080/realms/buildingflow */
  issuer: string;
  clientId: string;
}

function parseIdps(raw: string | undefined): IdentityProviderConfig[] {
  if (!raw) return [];
  try {
    const value = JSON.parse(raw) as unknown;
    if (!Array.isArray(value)) return [];
    return value.filter(
      (v): v is IdentityProviderConfig =>
        typeof v === 'object' && v !== null && 'id' in v && 'issuer' in v && 'clientId' in v && 'label' in v,
    );
  } catch {
    return [];
  }
}

export const hubConfig = {
  apiUrl: process.env.NEXT_PUBLIC_AIH_API_URL ?? 'http://localhost:28080',
  identityProviders: parseIdps(process.env.NEXT_PUBLIC_AIH_IDPS),
  returnOrigins: (process.env.NEXT_PUBLIC_AIH_HOST_RETURN_ORIGINS ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
  /** Yalnız yerel geliştirme; API'de AIH_AUTH_DEV_MODE=true olmalı. */
  devUser: process.env.NEXT_PUBLIC_AIH_DEV_USER || undefined,
};

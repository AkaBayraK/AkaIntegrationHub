import Keycloak from 'keycloak-js';
import type { IdentityProviderConfig } from './hub-config';

const REALM_SEGMENT = '/realms/';

export function keycloakFor(idp: IdentityProviderConfig): Keycloak {
  const index = idp.issuer.indexOf(REALM_SEGMENT);
  if (index === -1) throw new Error(`issuer '/realms/' içermeli: ${idp.issuer}`);
  return new Keycloak({
    url: idp.issuer.slice(0, index),
    realm: idp.issuer.slice(index + REALM_SEGMENT.length).replace(/\/+$/, ''),
    clientId: idp.clientId,
  });
}

const instances = new Map<string, { keycloak: Keycloak; ready: Promise<boolean> }>();

/**
 * Host uygulamada açık bir Keycloak oturumu varsa kullanıcı tekrar şifre girmeden geçer (SSO).
 * Token yalnız bellekte tutulur (THREAT_MODEL T-10).
 */
export function initIdentityProvider(idp: IdentityProviderConfig, locale: string): { keycloak: Keycloak; ready: Promise<boolean> } {
  const existing = instances.get(idp.id);
  if (existing) return existing;
  const keycloak = keycloakFor(idp);
  const ready = keycloak.init({ onLoad: 'login-required', pkceMethod: 'S256', checkLoginIframe: false, locale });
  const entry = { keycloak, ready };
  instances.set(idp.id, entry);
  return entry;
}

export async function freshToken(keycloak: Keycloak): Promise<string | null> {
  if (!keycloak.authenticated) return null;
  try {
    await keycloak.updateToken(30);
  } catch {
    await keycloak.login();
    return null;
  }
  return keycloak.token ?? null;
}

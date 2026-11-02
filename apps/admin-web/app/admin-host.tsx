'use client';

import {
  AkaIntegrationProvider,
  AppShell,
  HubSessionProvider,
  LoginShell,
  useTranslation,
  type AkaIntegrationAdapters,
  type Locale,
  type ThemeMode,
} from '@aka/integration-ui';
import type Keycloak from 'keycloak-js';
import { usePathname, useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import {
  loadStoredContext,
  mergeHostContext,
  parseHostContext,
  storeContext,
  type HostContext,
} from './lib/host-context';
import { hubConfig, type IdentityProviderConfig } from './lib/hub-config';
import { freshToken, initIdentityProvider } from './lib/oidc';

function IdpChooser({ onChoose }: { onChoose: (idp: IdentityProviderConfig) => void }) {
  const t = useTranslation();
  if (hubConfig.identityProviders.length === 0) {
    return <p className="aih-alert aih-alert--danger">NEXT_PUBLIC_AIH_IDPS</p>;
  }
  return (
    <div className="aih-row aih-row--wrap">
      {hubConfig.identityProviders.map((idp) => (
        <button key={idp.id} type="button" className="aih-button aih-button--primary" onClick={() => onChoose(idp)}>
          {t('login.submit')}: {idp.label}
        </button>
      ))}
    </div>
  );
}

function ReturnLink({ context }: { context: HostContext }) {
  if (!context.returnUrl) return null;
  const label = context.hostName ?? new URL(context.returnUrl).host;
  return (
    <a className="aih-host-return aih-nav-link" href={context.returnUrl}>
      ← {label}
    </a>
  );
}

export function AdminHost({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [context, setContext] = useState<HostContext>({
    idp: null,
    returnUrl: null,
    hostName: null,
    locale: null,
    theme: null,
  });
  const [locale, setLocale] = useState<Locale>('tr');
  const [mode, setMode] = useState<ThemeMode>('light');
  const [authenticated, setAuthenticated] = useState(Boolean(hubConfig.devUser));
  const [displayName, setDisplayName] = useState<string | undefined>(hubConfig.devUser);
  const keycloakRef = useRef<Keycloak | null>(null);

  const startLogin = useCallback(
    (idp: IdentityProviderConfig, currentLocale: string) => {
      const { keycloak, ready } = initIdentityProvider(idp, currentLocale);
      keycloakRef.current = keycloak;
      ready
        .then((ok) => {
          setAuthenticated(ok);
          const parsed = keycloak.tokenParsed as { name?: string; preferred_username?: string } | undefined;
          setDisplayName(parsed?.name ?? parsed?.preferred_username);
        })
        .catch(() => setAuthenticated(false));
    },
    [],
  );

  // İlk açılış: host bağlamını URL'den al, oturum boyunca sakla, IdP belliyse SSO ile giriş yap.
  useEffect(() => {
    const parsed = parseHostContext(
      window.location.search,
      hubConfig.returnOrigins,
      hubConfig.identityProviders.map((i) => i.id),
    );
    const merged = mergeHostContext(loadStoredContext(), parsed);
    storeContext(merged);
    setContext(merged);
    if (merged.locale) setLocale(merged.locale);
    if (merged.theme) setMode(merged.theme);
    if (!hubConfig.devUser && merged.idp) {
      const idp = hubConfig.identityProviders.find((i) => i.id === merged.idp);
      if (idp) startLogin(idp, merged.locale ?? 'tr');
    }
  }, [startLogin]);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  useEffect(() => {
    document.documentElement.dataset.aihTheme = mode;
  }, [mode]);

  const chooseIdp = useCallback(
    (idp: IdentityProviderConfig) => {
      const next = { ...context, idp: idp.id };
      storeContext(next);
      setContext(next);
      startLogin(idp, locale);
    },
    [context, locale, startLogin],
  );

  const getAccessToken = useCallback(async () => {
    const keycloak = keycloakRef.current;
    return keycloak ? freshToken(keycloak) : null;
  }, []);

  const adapters = useMemo<AkaIntegrationAdapters>(
    () => ({
      auth: {
        isAuthenticated: authenticated,
        displayName,
        getAccessToken,
        signIn: () => undefined,
        signOut: () => {
          if (keycloakRef.current) {
            void keycloakRef.current.logout({ redirectUri: context.returnUrl ?? window.location.origin });
          } else {
            setAuthenticated(false);
          }
        },
      },
      api: { baseUrl: hubConfig.apiUrl, devUser: hubConfig.devUser },
      locale: { locale, setLocale },
      theme: { mode, setMode },
      navigation: { currentPath: pathname, navigate: (path) => router.push(path) },
      tenant: { tenantId: null, projectId: null },
    }),
    [authenticated, displayName, getAccessToken, context.returnUrl, locale, mode, pathname, router],
  );

  return (
    <AkaIntegrationProvider adapters={adapters}>
      {authenticated ? (
        <AppShell headerExtra={<ReturnLink context={context} />}>
          <HubSessionProvider>{children}</HubSessionProvider>
        </AppShell>
      ) : (
        <LoginShell>
          {context.idp ? <p role="status">…</p> : <IdpChooser onChoose={chooseIdp} />}
        </LoginShell>
      )}
    </AkaIntegrationProvider>
  );
}

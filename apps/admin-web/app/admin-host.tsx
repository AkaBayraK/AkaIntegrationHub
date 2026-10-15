'use client';

import {
  AkaIntegrationProvider,
  AppShell,
  LoginShell,
  type AkaIntegrationAdapters,
  type Locale,
  type ThemeMode,
} from '@aka/integration-ui';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useMemo, useState, type ReactNode } from 'react';

export function AdminHost({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [locale, setLocale] = useState<Locale>('tr');
  const [mode, setMode] = useState<ThemeMode>('light');
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  useEffect(() => {
    document.documentElement.dataset.aihTheme = mode;
  }, [mode]);

  const adapters = useMemo<AkaIntegrationAdapters>(
    () => ({
      auth: {
        isAuthenticated: authenticated,
        getAccessToken: async () => null,
        signIn: () => setAuthenticated(true),
        signOut: () => setAuthenticated(false),
      },
      locale: { locale, setLocale },
      theme: { mode, setMode },
      navigation: { currentPath: pathname, navigate: (path) => router.push(path) },
      tenant: { tenantId: null, projectId: null },
    }),
    [authenticated, locale, mode, pathname, router],
  );

  return (
    <AkaIntegrationProvider adapters={adapters}>
      {authenticated ? <AppShell>{children}</AppShell> : <LoginShell />}
    </AkaIntegrationProvider>
  );
}

import { createContext, useContext, useMemo, type ReactNode } from 'react';
import { messages, type Locale, type MessageKey } from './i18n/messages';

export type ThemeMode = 'light' | 'dark';

export interface AuthAdapter {
  isAuthenticated: boolean;
  displayName?: string;
  getAccessToken: () => Promise<string | null>;
  signIn: () => void;
  signOut: () => void;
}

export interface LocaleAdapter {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export interface ThemeAdapter {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
}

export interface NavigationAdapter {
  currentPath: string;
  navigate: (path: string) => void;
}

export interface TenantAdapter {
  tenantId: string | null;
  projectId: string | null;
}

export interface AkaIntegrationAdapters {
  auth: AuthAdapter;
  locale: LocaleAdapter;
  theme: ThemeAdapter;
  navigation: NavigationAdapter;
  tenant: TenantAdapter;
}

const AkaIntegrationContext = createContext<AkaIntegrationAdapters | null>(null);

export function AkaIntegrationProvider({ adapters, children }: { adapters: AkaIntegrationAdapters; children: ReactNode }) {
  return <AkaIntegrationContext.Provider value={adapters}>{children}</AkaIntegrationContext.Provider>;
}

export function useAkaIntegration(): AkaIntegrationAdapters {
  const adapters = useContext(AkaIntegrationContext);
  if (!adapters) {
    throw new Error('useAkaIntegration must be used inside <AkaIntegrationProvider>');
  }
  return adapters;
}

export function useTranslation() {
  const { locale } = useAkaIntegration().locale;
  return useMemo(() => {
    const dictionary = messages[locale];
    return (key: MessageKey) => dictionary[key];
  }, [locale]);
}

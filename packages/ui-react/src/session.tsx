import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { createHubClient, type HubClient } from './api/client';
import type { Me } from './api/types';
import { useAkaIntegration } from './context';

export function useHubClient(): HubClient {
  const { auth, api } = useAkaIntegration();
  if (!api) throw new Error('AkaIntegrationAdapters.api (Hub API adresi) tanımlı değil');
  const { baseUrl, devUser } = api;
  const getAccessToken = auth.getAccessToken;
  return useMemo(() => createHubClient({ baseUrl, devUser, getAccessToken }), [baseUrl, devUser, getAccessToken]);
}

interface HubSession {
  me: Me | null;
  loading: boolean;
  error: Error | null;
  can: (permission: string) => boolean;
  reload: () => void;
}

const HubSessionContext = createContext<HubSession | null>(null);

/** Oturumdaki kullanıcıyı, tenant'ı ve izinleri (/v1/me) bir kez yükler. */
export function HubSessionProvider({ children }: { children: ReactNode }) {
  const client = useHubClient();
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    client
      .me()
      .then((value) => {
        if (!cancelled) {
          setMe(value);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err : new Error(String(err)));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [client, nonce]);

  const can = useCallback((permission: string) => Boolean(me?.permissions.includes(permission)), [me]);
  const reload = useCallback(() => setNonce((n) => n + 1), []);
  const value = useMemo(() => ({ me, loading, error, can, reload }), [me, loading, error, can, reload]);
  return <HubSessionContext.Provider value={value}>{children}</HubSessionContext.Provider>;
}

export function useHubSession(): HubSession {
  const session = useContext(HubSessionContext);
  if (!session) throw new Error('useHubSession must be used inside <HubSessionProvider>');
  return session;
}

import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { CacheAccount } from '../../api/types';
import { AkaIntegrationProvider, type AkaIntegrationAdapters } from '../../context';
import { HubSessionProvider } from '../../session';
import { safeConsoleUrl } from '../console/ConsolePanel';
import { validateCacheForm } from './CacheAccountForm';
import { CacheAccountsPage } from './CacheAccountsPage';

const TENANT = '11111111-1111-1111-1111-111111111111';

const ACCOUNT: CacheAccount = {
  id: 'cache-1', tenantId: TENANT, projectId: null, name: 'Yerel Valkey', providerType: 'valkey', host: 'localhost',
  port: 26379, tlsEnabled: false, authMode: 'none', username: null, hasSecret: false, databaseIndex: 0,
  keyPrefix: 'buildingflow:', environment: 'test', enabled: true, isDefault: true, timeoutSeconds: 5,
  consoleUrl: 'http://localhost:5540', lastTestAt: null, lastTestOutcome: null, serverVersion: null, version: 1,
  license: null, licenseStatus: 'not_required',
  createdAt: '2026-11-03T10:00:00Z', updatedAt: '2026-11-03T10:00:00Z',
};

const TEST_RESULT = {
  accountId: 'cache-1', outcome: 'passed', errorCode: null, durationMs: 4,
  steps: [{ step: 'ping', outcome: 'passed', durationMs: 1, errorCode: null }],
  server: {
    serverName: 'valkey', version: '8.1.4', mode: 'standalone', role: 'master', uptimeSeconds: 90000,
    connectedClients: 3, usedMemory: '1.20M', maxMemory: '0B', evictionPolicy: 'noeviction', keyspace: { db0: 12 },
  },
};

function renderPage(permissions: string[], account: CacheAccount = ACCOUNT) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input));
    const body = url.pathname === '/v1/me'
      ? { subject: 'u1', displayName: null, email: null, tenant: { id: TENANT, slug: 'bf', name: 'BuildingFlow' }, roles: [], permissions }
      : init?.method === 'POST'
        ? TEST_RESULT
        : { items: [account], nextCursor: null };
    return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
  });
  vi.stubGlobal('fetch', fetchMock);
  const adapters: AkaIntegrationAdapters = {
    auth: { isAuthenticated: true, getAccessToken: async () => 'token', signIn: vi.fn(), signOut: vi.fn() },
    api: { baseUrl: 'http://hub.test' },
    locale: { locale: 'tr', setLocale: vi.fn() },
    theme: { mode: 'light', setMode: vi.fn() },
    navigation: { currentPath: '/admin/cache/providers', navigate: vi.fn() },
    tenant: { tenantId: null, projectId: null },
  };
  render(
    <AkaIntegrationProvider adapters={adapters}>
      <HubSessionProvider>
        <CacheAccountsPage />
      </HubSessionProvider>
    </AkaIntegrationProvider>,
  );
  return fetchMock;
}

describe('CacheAccountsPage', () => {
  it('tests the connection and shows the server summary', async () => {
    const fetchMock = renderPage(['cache-account:read', 'cache-account:write', 'cache-account:test']);
    fireEvent.click(await screen.findByRole('button', { name: 'Bağlantı testi: Yerel Valkey' }));

    const summary = await screen.findByLabelText('Sunucu özeti');
    expect(within(summary).getByText('valkey 8.1.4')).toBeInTheDocument();
    expect(within(summary).getByText('12')).toBeInTheDocument();
    expect(within(summary).getByText('1 g 1 sa')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      'http://hub.test/v1/tenants/11111111-1111-1111-1111-111111111111/cache-accounts/cache-1/test-connection',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('shows the declared Redis license and its status', async () => {
    renderPage(['cache-account:read'], {
      ...ACCOUNT,
      providerType: 'redis',
      licenseStatus: 'expiring',
      license: {
        type: 'redis-enterprise', holder: 'Aka Yazılım', reference: 'SUB-1', expiresOn: '2026-11-20', hasKey: true,
        acknowledgedAt: '2026-11-03T10:00:00Z', acknowledgedBy: 'ayse',
      },
    });
    const section = (await screen.findByLabelText('Redis lisansı'));
    expect(within(section).getByText('Redis Enterprise (ticari)')).toBeInTheDocument();
    expect(within(section).getByText('Şifreli olarak kayıtlı')).toBeInTheDocument();
    expect(screen.getAllByText('Lisans bitmek üzere').length).toBeGreaterThan(0);
  });

  it('opens the management console in a new tab or embeds it on demand', async () => {
    renderPage(['cache-account:read']);
    const open = await screen.findByRole('link', { name: /Yeni sekmede aç/ });
    expect(open).toHaveAttribute('href', 'http://localhost:5540/');
    expect(open).toHaveAttribute('target', '_blank');
    expect(open).toHaveAttribute('rel', 'noopener noreferrer');
    expect(screen.queryByRole('button', { name: /Bağlantı testi/ })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Ekranda göster' }));
    expect(screen.getByTitle('Yönetim arayüzü: Yerel Valkey')).toHaveAttribute('sandbox');
  });
});

describe('cache form rules', () => {
  const base = {
    name: 'Valkey', providerType: 'valkey' as const, host: 'localhost', port: 6379, tlsEnabled: false,
    authMode: 'none' as const, username: '', password: '', databaseIndex: 0, keyPrefix: '', environment: 'test' as const,
    enabled: true, makeDefault: false, timeoutSeconds: 5, consoleUrl: '',
    license: { type: 'agpl-3.0' as const, holder: '', reference: '', expiresOn: '', key: '', acknowledged: false },
  };

  it('accepts a minimal test account and enforces auth, database and prefix rules', () => {
    expect(validateCacheForm(base, { creating: true, hasSecret: false })).toEqual({});
    expect(validateCacheForm({ ...base, environment: 'production' }, { creating: true, hasSecret: false }).authMode).toBe(
      'cache.form.error.prodAuth',
    );
    expect(validateCacheForm({ ...base, authMode: 'acl' }, { creating: true, hasSecret: false })).toMatchObject({
      username: 'smtp.form.error.required',
      password: 'smtp.form.error.required',
    });
    expect(validateCacheForm({ ...base, authMode: 'password' }, { creating: false, hasSecret: true }).password).toBeUndefined();
    expect(validateCacheForm({ ...base, databaseIndex: 16, keyPrefix: 'bad prefix' }, { creating: true, hasSecret: false }))
      .toMatchObject({ databaseIndex: 'cache.form.error.database', keyPrefix: 'cache.form.error.prefix' });
    expect(validateCacheForm({ ...base, consoleUrl: 'javascript:alert(1)' }, { creating: true, hasSecret: false }).consoleUrl)
      .toBe('console.error.url');
  });

  it('requires a declared license for Redis and a key for commercial licenses', () => {
    const redis = { ...base, providerType: 'redis' as const };
    expect(validateCacheForm(redis, { creating: true, hasSecret: false }).licenseAck).toBe('license.error.ack');
    expect(
      validateCacheForm({ ...redis, license: { ...redis.license, acknowledged: true } }, { creating: true, hasSecret: false }),
    ).toEqual({});
    const enterprise = { ...redis, license: { ...redis.license, type: 'redis-enterprise' as const, acknowledged: true } };
    expect(validateCacheForm(enterprise, { creating: true, hasSecret: false })).toMatchObject({
      licenseHolder: 'smtp.form.error.required',
      licenseKey: 'smtp.form.error.required',
    });
    const stored = { ...enterprise, license: { ...enterprise.license, holder: 'Aka' } };
    expect(validateCacheForm(stored, { creating: false, hasSecret: false, hasLicenseKey: true })).toEqual({});
  });

  it('only allows http(s) console addresses', () => {
    expect(safeConsoleUrl('https://ui.example.com/x')?.host).toBe('ui.example.com');
    expect(safeConsoleUrl('javascript:alert(1)')).toBeNull();
    expect(safeConsoleUrl('not a url')).toBeNull();
    expect(safeConsoleUrl(null)).toBeNull();
  });
});

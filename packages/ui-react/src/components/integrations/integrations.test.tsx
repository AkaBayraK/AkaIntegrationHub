import { fireEvent, render, screen, within } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import type { SmtpAccount } from '../../api/types';
import { AkaIntegrationProvider, type AkaIntegrationAdapters } from '../../context';
import { HubSessionProvider } from '../../session';
import { IntegrationsHome } from './IntegrationsHome';

const TENANT = '11111111-1111-1111-1111-111111111111';

const HEALTHY: SmtpAccount = {
  id: 'acc-1', tenantId: TENANT, projectId: null, name: 'Kurumsal Bildirim', providerType: 'microsoft_365',
  host: 'smtp.office365.com', port: 587, tlsMode: 'starttls', authMode: 'smtp_auth', username: 'u', hasSecret: true,
  senderAddress: 'noreply@example.com', senderName: null, replyTo: null, environment: 'production', enabled: true,
  isDefault: true, priority: 1, timeoutSeconds: 30, rateLimitPerMinute: null, consoleUrl: null, lastTestAt: '2026-11-02T10:00:00Z',
  lastTestOutcome: 'passed', lastSuccessSendAt: null, version: 1, createdAt: '2026-11-02T10:00:00Z', createdBy: 'u',
  updatedAt: '2026-11-02T10:00:00Z', updatedBy: 'u',
};

const FAILING: SmtpAccount = {
  ...HEALTHY, id: 'acc-2', name: 'Destek Ekibi', providerType: 'google_workspace', environment: 'test',
  isDefault: false, lastTestOutcome: 'failed',
};

function render_(permissions: string[], accounts: SmtpAccount[], navigate = vi.fn()) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input));
      const body = url.pathname === '/v1/me'
        ? { subject: 'u1', displayName: null, email: null, tenant: { id: TENANT, slug: 'bf', name: 'BuildingFlow' }, roles: [], permissions }
        : url.pathname.endsWith('/cache-accounts')
          ? { items: [{ id: 'cache-1' }], nextCursor: null }
          : { items: accounts, nextCursor: null };
      return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }),
  );
  const adapters: AkaIntegrationAdapters = {
    auth: { isAuthenticated: true, getAccessToken: async () => 'token', signIn: vi.fn(), signOut: vi.fn() },
    api: { baseUrl: 'http://hub.test' },
    locale: { locale: 'tr', setLocale: vi.fn() },
    theme: { mode: 'light', setMode: vi.fn() },
    navigation: { currentPath: '/', navigate },
    tenant: { tenantId: null, projectId: null },
  };
  const wrap = (children: ReactNode) => (
    <AkaIntegrationProvider adapters={adapters}>
      <HubSessionProvider>{children}</HubSessionProvider>
    </AkaIntegrationProvider>
  );
  render(wrap(<IntegrationsHome />));
  return navigate;
}

const ADMIN = ['smtp-account:read', 'smtp-account:write', 'cache-account:read'];

describe('IntegrationsHome', () => {
  it('shows integration types, marks unbuilt ones as coming soon and opens the email page', async () => {
    const navigate = render_(ADMIN, [HEALTHY, FAILING]);
    await screen.findByText('Destek Ekibi');
    const types = screen.getByRole('region', { name: 'Yeni entegrasyon ekle' });
    const email = within(types).getByRole('link', { name: /E-posta \(SMTP\)/ });
    expect(email.closest('.aih-type')).toHaveTextContent('2 tanımlı');
    expect(screen.getByText('Mesaj Kuyruğu').closest('.aih-type')).toHaveTextContent('Yakında');
    expect(within(types).getByRole('link', { name: /Cache \(Valkey \/ Redis\)/ }).closest('.aih-type')).toHaveTextContent('1 tanımlı');

    fireEvent.click(email);
    expect(navigate).toHaveBeenCalledWith('/admin/email/providers');
    fireEvent.click(screen.getByRole('button', { name: 'Ekle: E-posta (SMTP)' }));
    expect(navigate).toHaveBeenCalledWith('/admin/email/providers/new');
  });

  it('lists configured integrations with health and filters problems', async () => {
    render_(ADMIN, [HEALTHY, FAILING]);
    const failing = (await screen.findByText('Destek Ekibi')).closest('article')!;
    expect(within(failing).getByText('Test başarısız')).toBeInTheDocument();
    expect(within(failing).getByRole('button', { name: 'Sorunu gider' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Sorunlu · 1' }));
    expect(screen.queryByText('Kurumsal Bildirim')).not.toBeInTheDocument();
    expect(screen.getByText('Destek Ekibi')).toBeInTheDocument();
  });

  it('reorders integration types in edit mode and remembers the order', async () => {
    window.localStorage.clear();
    render_(ADMIN, [HEALTHY]);
    await screen.findByText('Kurumsal Bildirim');
    const types = screen.getByRole('region', { name: 'Yeni entegrasyon ekle' });
    const names = () => within(types).getAllByText(/^(E-posta \(SMTP\)|Cache \(Valkey \/ Redis\))$/).map((n) => n.textContent);
    expect(names()).toEqual(['E-posta (SMTP)', 'Cache (Valkey / Redis)']);

    fireEvent.click(screen.getByRole('button', { name: 'Düzeni değiştir' }));
    fireEvent.click(screen.getByRole('button', { name: 'Arkaya al: E-posta (SMTP)' }));

    expect(names()).toEqual(['Cache (Valkey / Redis)', 'E-posta (SMTP)']);
    expect(window.localStorage.getItem('aih.layout.hub-types.u1')).toContain('"cache"');

    fireEvent.click(screen.getByRole('button', { name: 'Varsayılana dön' }));
    expect(names()).toEqual(['E-posta (SMTP)', 'Cache (Valkey / Redis)']);
    fireEvent.click(screen.getByRole('button', { name: 'Bitti' }));
    expect(screen.queryByRole('button', { name: 'Arkaya al: E-posta (SMTP)' })).not.toBeInTheDocument();
  });

  it('hides the add action for viewers', async () => {
    render_(['smtp-account:read'], []);
    expect(await screen.findByText(/Henüz tanımlı entegrasyon yok/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Ekle: E-posta (SMTP)' })).not.toBeInTheDocument();
  });
});

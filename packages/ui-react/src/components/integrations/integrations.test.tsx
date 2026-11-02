import { fireEvent, render, screen, within } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import type { SmtpAccount } from '../../api/types';
import { AkaIntegrationProvider, type AkaIntegrationAdapters } from '../../context';
import { HubSessionProvider } from '../../session';
import { smtpHealth } from './catalog';
import { IntegrationsHome } from './IntegrationsHome';

const TENANT = '11111111-1111-1111-1111-111111111111';

function account(overrides: Partial<SmtpAccount>): SmtpAccount {
  return {
    id: 'a', tenantId: TENANT, projectId: null, name: 'Hesap', providerType: 'custom_smtp', host: 'smtp.example.com',
    port: 587, tlsMode: 'starttls', authMode: 'smtp_auth', username: 'u', hasSecret: true,
    senderAddress: 'noreply@example.com', senderName: null, replyTo: null, environment: 'production', enabled: true,
    isDefault: false, priority: 100, timeoutSeconds: 15, rateLimitPerMinute: null, lastTestAt: null,
    lastTestOutcome: null, lastSuccessSendAt: null, version: 1, createdAt: '2026-11-02T10:00:00Z', createdBy: 'u',
    updatedAt: '2026-11-02T10:00:00Z', updatedBy: 'u', ...overrides,
  };
}

const ACCOUNTS = [
  account({ id: 'ok', name: 'Bildirim hesabı', lastTestOutcome: 'passed', isDefault: true }),
  account({ id: 'bad', name: 'Fatura gönderimi', lastTestOutcome: 'failed' }),
  account({ id: 'tst', name: 'Deneme kutusu', environment: 'test', providerType: 'mailpit_test' }),
];

function render_(permissions: string[], navigate = vi.fn(), items = ACCOUNTS) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = new URL(String(input));
    const body =
      url.pathname === '/v1/me'
        ? { subject: 'u', displayName: null, email: null, tenant: { id: TENANT, slug: 'b', name: 'B' }, roles: [], permissions }
        : { items, nextCursor: null };
    return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
  });
  vi.stubGlobal('fetch', fetchMock);
  const adapters: AkaIntegrationAdapters = {
    auth: { isAuthenticated: true, getAccessToken: async () => 't', signIn: vi.fn(), signOut: vi.fn() },
    api: { baseUrl: 'http://hub.test' },
    locale: { locale: 'tr', setLocale: vi.fn() },
    theme: { mode: 'light', setMode: vi.fn() },
    navigation: { currentPath: '/', navigate },
    tenant: { tenantId: null, projectId: null },
  };
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <AkaIntegrationProvider adapters={adapters}>
      <HubSessionProvider>{children}</HubSessionProvider>
    </AkaIntegrationProvider>
  );
  render(<IntegrationsHome />, { wrapper: Wrapper });
  return { navigate, fetchMock };
}

const ADMIN = ['smtp-account:read', 'smtp-account:write'];

describe('smtpHealth', () => {
  it('derives health from enabled state and last test', () => {
    expect(smtpHealth({ enabled: false, lastTestOutcome: 'passed' })).toBe('disabled');
    expect(smtpHealth({ enabled: true, lastTestOutcome: 'failed' })).toBe('failed');
    expect(smtpHealth({ enabled: true, lastTestOutcome: 'passed' })).toBe('healthy');
    expect(smtpHealth({ enabled: true, lastTestOutcome: null })).toBe('untested');
  });
});

describe('IntegrationsHome', () => {
  it('shows type tiles with the SMTP count and coming-soon types', async () => {
    const { navigate } = render_(ADMIN);
    const tiles = await screen.findByRole('region', { name: 'Yeni entegrasyon ekle' });
    expect(await within(tiles).findByText('3 tanımlı')).toBeInTheDocument();
    expect(within(tiles).getAllByText('Yakında')).toHaveLength(7);
    expect(within(tiles).queryByRole('link', { name: 'Cache (Redis / Valkey)' })).not.toBeInTheDocument();
    fireEvent.click(within(tiles).getByRole('link', { name: 'E-posta (SMTP)' }));
    expect(navigate).toHaveBeenCalledWith('/admin/email/providers');
    fireEvent.click(within(tiles).getByRole('button', { name: 'Ekle: E-posta (SMTP)' }));
    expect(navigate).toHaveBeenCalledWith('/admin/email/providers/new');
  });

  it('lists defined connections with health and filters problems', async () => {
    const { navigate } = render_(ADMIN);
    const defined = await screen.findByRole('region', { name: 'Tanımlı entegrasyonlar' });
    expect(await within(defined).findByText('Bildirim hesabı')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('1/3 sağlıklı');
    expect(screen.getByRole('status')).toHaveTextContent('1 sorunlu');

    fireEvent.click(within(defined).getByRole('button', { name: 'Sorunlu' }));
    expect(within(defined).queryByText('Bildirim hesabı')).not.toBeInTheDocument();
    fireEvent.click(within(defined).getByRole('button', { name: 'Sorunu gider: Fatura gönderimi' }));
    expect(navigate).toHaveBeenCalledWith('/admin/email/providers?account=bad');

    fireEvent.click(within(defined).getByRole('button', { name: 'Test' }));
    expect(within(defined).getByText('Deneme kutusu')).toBeInTheDocument();
    expect(within(defined).queryByText('Fatura gönderimi')).not.toBeInTheDocument();
  });

  it('hides add buttons for read-only users and shows empty state', async () => {
    render_(['smtp-account:read'], vi.fn(), []);
    expect(await screen.findByText(/Henüz tanımlı entegrasyon yok/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^Ekle:/ })).not.toBeInTheDocument();
  });

  it('does not request accounts without read permission', async () => {
    const { fetchMock } = render_([]);
    expect(await screen.findByText('Bu ekranı görüntüleme yetkiniz yok.')).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([u]) => String(u).includes('/smtp-accounts'))).toBe(false);
  });
});

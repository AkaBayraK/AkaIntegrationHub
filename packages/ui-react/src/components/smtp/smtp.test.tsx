import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import type { SmtpAccount, SmtpCapability } from '../../api/types';
import { AkaIntegrationProvider, type AkaIntegrationAdapters } from '../../context';
import { HubSessionProvider } from '../../session';
import { SmtpAccountForm, validateSmtpForm } from './SmtpAccountForm';
import { SmtpAccountsPage } from './SmtpAccountsPage';

const TENANT = '11111111-1111-1111-1111-111111111111';

const ACCOUNT: SmtpAccount = {
  id: 'acc-1',
  tenantId: TENANT,
  projectId: null,
  name: 'Kurumsal SMTP',
  providerType: 'custom_smtp',
  host: 'smtp.example.com',
  port: 587,
  tlsMode: 'starttls',
  authMode: 'smtp_auth',
  username: 'mailer@example.com',
  hasSecret: true,
  senderAddress: 'noreply@example.com',
  senderName: 'Example',
  replyTo: null,
  environment: 'production',
  enabled: true,
  isDefault: true,
  priority: 100,
  timeoutSeconds: 15,
  rateLimitPerMinute: null,
  lastTestAt: null,
  lastTestOutcome: null,
  lastSuccessSendAt: null,
  version: 3,
  createdAt: '2026-11-02T10:00:00Z',
  createdBy: 'u',
  updatedAt: '2026-11-02T10:00:00Z',
  updatedBy: 'u',
};

const CAPS: SmtpCapability[] = [
  {
    type: 'custom_smtp', label: 'Custom SMTP', defaultHost: null, defaultPort: 587, defaultTls: 'starttls',
    tlsModes: ['starttls', 'implicit', 'none'], authModes: ['smtp_auth', 'none'], plannedAuthModes: [],
    environments: ['test', 'production'], notes: '',
  },
  {
    type: 'microsoft_365', label: 'Microsoft 365', defaultHost: 'smtp.office365.com', defaultPort: 587,
    defaultTls: 'starttls', tlsModes: ['starttls'], authModes: ['smtp_auth'], plannedAuthModes: ['oauth2'],
    environments: ['test', 'production'], notes: 'OAuth2 sonraki dilimde.',
  },
];

function me(permissions: string[]) {
  return {
    subject: 'u1', displayName: 'Ayşe', email: 'ayse@example.com',
    tenant: { id: TENANT, slug: 'building', name: 'BuildingFlow' },
    roles: ['TenantAdmin'], permissions,
  };
}

const ADMIN = ['smtp-account:read', 'smtp-account:write', 'smtp-account:test', 'smtp-account:send-test'];

type Handler = (url: URL, init: RequestInit) => { status?: number; body: unknown };

function mockFetch(handler: Handler) {
  return vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = new URL(String(input));
    const { status = 200, body } = handler(url, init);
    return new Response(body === undefined ? '' : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  });
}

function Host({ children, fetchMock, navigate = vi.fn() }: { children: ReactNode; fetchMock: typeof fetch; navigate?: (p: string) => void }) {
  vi.stubGlobal('fetch', fetchMock);
  const adapters: AkaIntegrationAdapters = {
    auth: { isAuthenticated: true, getAccessToken: async () => 'token-123', signIn: vi.fn(), signOut: vi.fn() },
    api: { baseUrl: 'http://hub.test' },
    locale: { locale: 'tr', setLocale: vi.fn() },
    theme: { mode: 'light', setMode: vi.fn() },
    navigation: { currentPath: '/admin/email/providers', navigate },
    tenant: { tenantId: null, projectId: null },
  };
  return (
    <AkaIntegrationProvider adapters={adapters}>
      <HubSessionProvider>{children}</HubSessionProvider>
    </AkaIntegrationProvider>
  );
}

describe('SmtpAccountsPage', () => {
  it('lists accounts with bearer token and shows actions for admins', async () => {
    const fetchMock = mockFetch((url) => {
      if (url.pathname === '/v1/me') return { body: me(ADMIN) };
      return { body: { items: [ACCOUNT], nextCursor: null } };
    });
    render(<Host fetchMock={fetchMock}><SmtpAccountsPage /></Host>);

    const row = await screen.findByRole('row', { name: /Kurumsal SMTP/ });
    expect(within(row).getByText('Varsayılan')).toBeInTheDocument();
    expect(within(row).getByText('smtp.example.com:587')).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'Bağlantı testi: Kurumsal SMTP' })).toBeInTheDocument();
    expect(within(row).queryByRole('button', { name: /Varsayılan yap/ })).not.toBeInTheDocument();
    const [, init] = fetchMock.mock.calls.find(([u]) => String(u).includes('/smtp-accounts'))!;
    expect((init!.headers as Record<string, string>).Authorization).toBe('Bearer token-123');
  });

  it('hides write actions for viewers', async () => {
    const fetchMock = mockFetch((url) =>
      url.pathname === '/v1/me' ? { body: me(['smtp-account:read']) } : { body: { items: [ACCOUNT], nextCursor: null } },
    );
    render(<Host fetchMock={fetchMock}><SmtpAccountsPage /></Host>);
    await screen.findByRole('row', { name: /Kurumsal SMTP/ });
    expect(screen.queryByRole('button', { name: 'Yeni hesap' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Bağlantı testi/ })).not.toBeInTheDocument();
  });

  it('runs a connection test and renders steps', async () => {
    const fetchMock = mockFetch((url, init) => {
      if (url.pathname === '/v1/me') return { body: me(ADMIN) };
      if (url.pathname.endsWith('/test-connection') && init.method === 'POST') {
        return {
          body: {
            id: 't1', accountId: 'acc-1', testType: 'connection', outcome: 'failed', errorCode: 'SMTP_AUTH_FAILED',
            durationMs: 40, createdAt: '2026-11-02T10:00:00Z',
            steps: [
              { step: 'dns', outcome: 'passed', durationMs: 1, errorCode: null },
              { step: 'auth', outcome: 'failed', durationMs: 20, errorCode: null },
            ],
          },
        };
      }
      return { body: { items: [ACCOUNT], nextCursor: null } };
    });
    render(<Host fetchMock={fetchMock}><SmtpAccountsPage /></Host>);
    fireEvent.click(await screen.findByRole('button', { name: 'Bağlantı testi: Kurumsal SMTP' }));
    expect(await screen.findByText('Kimlik doğrulama')).toBeInTheDocument();
    expect(screen.getByText('SMTP_AUTH_FAILED')).toBeInTheDocument();
    expect(screen.getByText('Bağlantı testi e-posta göndermez.')).toBeInTheDocument();
  });

  it('requires explicit confirmation before sending a test email', async () => {
    const fetchMock = mockFetch((url, init) => {
      if (url.pathname === '/v1/me') return { body: me(ADMIN) };
      if (url.pathname.endsWith('/send-test-email')) {
        expect((init.headers as Record<string, string>)['Idempotency-Key']).toMatch(/^ui-/);
        return { body: { id: 'd1', status: 'accepted_by_smtp', lastErrorCode: null } };
      }
      return { body: { items: [ACCOUNT], nextCursor: null } };
    });
    render(<Host fetchMock={fetchMock}><SmtpAccountsPage /></Host>);
    fireEvent.click(await screen.findByRole('button', { name: 'Test e-postası: Kurumsal SMTP' }));
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByLabelText('Alıcı')).toHaveValue('ayse@example.com');
    const send = within(dialog).getByRole('button', { name: 'Gönder' });
    expect(send).toBeDisabled();
    fireEvent.click(within(dialog).getByRole('checkbox'));
    fireEvent.click(send);
    expect(await screen.findByText(/alıcıya teslim edildiği anlamına gelmez/)).toBeInTheDocument();
  });

  it('shows the correlation id when the API fails', async () => {
    const fetchMock = mockFetch((url) =>
      url.pathname === '/v1/me'
        ? { body: me(ADMIN) }
        : { status: 500, body: { status: 500, code: 'AIH-COMMON-500', correlationId: 'corr-12345678' } },
    );
    render(<Host fetchMock={fetchMock}><SmtpAccountsPage /></Host>);
    expect(await screen.findByRole('alert')).toHaveTextContent('corr-12345678');
  });
});

describe('SmtpAccountForm', () => {
  it('validates production TLS, port/TLS pairing and required password', () => {
    const base = {
      name: 'x', providerType: 'custom_smtp' as const, host: 'h', port: 465, tlsMode: 'starttls' as const,
      authMode: 'smtp_auth' as const, username: 'u', password: '', senderAddress: 'bad', senderName: '',
      replyTo: '', environment: 'production' as const, enabled: true, makeDefault: false, priority: 1,
      timeoutSeconds: 15, rateLimitPerMinute: null,
    };
    const errors = validateSmtpForm(base, { creating: true, hasSecret: false });
    expect(errors.port).toBe('smtp.form.error.portTls');
    expect(errors.password).toBe('smtp.form.error.required');
    expect(errors.senderAddress).toBe('smtp.form.error.email');
    expect(validateSmtpForm({ ...base, tlsMode: 'none', port: 25 }, { creating: true, hasSecret: false }).tlsMode).toBe(
      'smtp.form.error.prodTls',
    );
    expect(validateSmtpForm(base, { creating: false, hasSecret: true }).password).toBeUndefined();
  });

  it('prefills provider defaults and creates an account with the password', async () => {
    const navigate = vi.fn();
    let created: Record<string, unknown> | null = null;
    const fetchMock = mockFetch((url, init) => {
      if (url.pathname === '/v1/me') return { body: me(ADMIN) };
      if (url.pathname === '/v1/provider-types/smtp') return { body: CAPS };
      if (init.method === 'POST') {
        created = JSON.parse(String(init.body));
        return { status: 201, body: { ...ACCOUNT, id: 'new' } };
      }
      return { body: {} };
    });
    render(<Host fetchMock={fetchMock} navigate={navigate}><SmtpAccountForm /></Host>);
    fireEvent.change(await screen.findByLabelText('Sağlayıcı tipi'), { target: { value: 'microsoft_365' } });
    expect(screen.getByLabelText('Sunucu (host)')).toHaveValue('smtp.office365.com');
    expect(screen.getByRole('option', { name: 'OAuth2' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Hesap adı'), { target: { value: 'M365' } });
    fireEvent.change(screen.getByLabelText('Kullanıcı adı'), { target: { value: 'ops@example.com' } });
    fireEvent.change(screen.getByLabelText('Şifre'), { target: { value: 's3cret!' } });
    fireEvent.change(screen.getByLabelText('Gönderen adresi'), { target: { value: 'noreply@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: 'Kaydet' }));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/admin/email/providers'));
    expect(created).toMatchObject({ providerType: 'microsoft_365', password: 's3cret!', host: 'smtp.office365.com' });
  });

  it('never prefills the stored password and sends If-Match on edit', async () => {
    const calls: { method: string; path: string; headers: Record<string, string> }[] = [];
    const fetchMock = mockFetch((url, init) => {
      calls.push({ method: init.method ?? 'GET', path: url.pathname, headers: init.headers as Record<string, string> });
      if (url.pathname === '/v1/me') return { body: me(ADMIN) };
      if (url.pathname === '/v1/provider-types/smtp') return { body: CAPS };
      if (init.method === 'PATCH') return { status: 412, body: { status: 412, code: 'AIH-COMMON-412' } };
      return { body: ACCOUNT };
    });
    render(<Host fetchMock={fetchMock}><SmtpAccountForm accountId="acc-1" /></Host>);
    const password = await screen.findByLabelText('Yeni şifre (değiştirmek için doldurun)');
    expect(password).toHaveValue('');
    expect(screen.getByText(/Kayıtlı bir şifre var/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Kaydet' }));
    expect(await screen.findByText(/başka biri tarafından değiştirildi/)).toBeInTheDocument();
    expect(calls.find((c) => c.method === 'PATCH')!.headers['If-Match']).toBe('W/"3"');
  });
});

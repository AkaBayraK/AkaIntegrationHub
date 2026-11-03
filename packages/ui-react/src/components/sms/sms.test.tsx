import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { SmsAccount } from '../../api/types';
import { AkaIntegrationProvider, type AkaIntegrationAdapters } from '../../context';
import { HubSessionProvider } from '../../session';
import { validateSmsForm, type SmsFormState } from './SmsAccountForm';
import { SmsAccountsPage } from './SmsAccountsPage';

const TENANT = '11111111-1111-1111-1111-111111111111';

const ACCOUNT: SmsAccount = {
  id: 'sms-1', tenantId: TENANT, projectId: null, name: 'BuildingFlow SMS', providerType: 'netgsm',
  senderHeader: 'BLDFLOW', username: '8501234567', hasSecret: true, environment: 'production', enabled: true,
  isDefault: true, creditBalance: 40, lowCreditThreshold: 100, lowCredit: true, consoleUrl: null,
  lastTestAt: null, lastTestOutcome: 'passed', version: 3, createdAt: '2026-11-03T10:00:00Z', updatedAt: '2026-11-03T10:00:00Z',
};

const MESSAGE = {
  id: 'm-1', accountId: 'sms-1', kind: 'api', purpose: 'operational', typeCode: 'DUES', referenceType: null, referenceId: null,
  phoneMasked: '+90532*****67', segments: 1, creditCost: 1, status: 'failed', providerType: 'netgsm', providerMessageId: null,
  errorCode: 'SMS_SENDER_REJECTED', correlationId: null, durationMs: 120, createdBy: 'bf', createdAt: '2026-11-03T10:05:00Z',
};

function renderPage(permissions: string[]) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input));
    let body: unknown;
    if (url.pathname === '/v1/me') {
      body = { subject: 'u1', displayName: null, email: null, tenant: { id: TENANT, slug: 'bf', name: 'BuildingFlow' }, roles: [], permissions };
    } else if (url.pathname.endsWith('/credits') && init?.method === 'POST') {
      body = { ...ACCOUNT, creditBalance: 1040, lowCredit: false };
    } else if (url.pathname.endsWith('/credits')) {
      body = [{ id: 'c1', kind: 'load', quantity: 50, balanceAfter: 50, reason: 'Kasım', messageId: null, createdBy: 'u1', createdAt: '2026-11-03T09:00:00Z' }];
    } else if (url.pathname.endsWith('/sms/messages')) {
      body = { items: [MESSAGE], nextCursor: null };
    } else {
      body = { items: [ACCOUNT], nextCursor: null };
    }
    return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
  });
  vi.stubGlobal('fetch', fetchMock);
  const adapters: AkaIntegrationAdapters = {
    auth: { isAuthenticated: true, getAccessToken: async () => 'token', signIn: vi.fn(), signOut: vi.fn() },
    api: { baseUrl: 'http://hub.test' },
    locale: { locale: 'tr', setLocale: vi.fn() },
    theme: { mode: 'light', setMode: vi.fn() },
    navigation: { currentPath: '/admin/sms/providers', navigate: vi.fn() },
    tenant: { tenantId: null, projectId: null },
  };
  render(
    <AkaIntegrationProvider adapters={adapters}>
      <HubSessionProvider>
        <SmsAccountsPage />
      </HubSessionProvider>
    </AkaIntegrationProvider>,
  );
  return fetchMock;
}

describe('SmsAccountsPage', () => {
  it('shows balance, low-credit warning, recent messages and credit history', async () => {
    renderPage(['sms-account:read', 'sms-message:read']);

    expect((await screen.findAllByText('Kontör azaldı')).length).toBeGreaterThan(0);
    expect(await screen.findByText('SMS_SENDER_REJECTED')).toBeInTheDocument();
    expect(screen.getByText('+90532*****67')).toBeInTheDocument();
    expect(screen.getByText('Kasım')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Kontör yükle/ })).not.toBeInTheDocument();
  });

  it('loads credit through the credits endpoint', async () => {
    const fetchMock = renderPage(['sms-account:read', 'sms-message:read', 'sms-credit:manage']);
    fireEvent.click(await screen.findByRole('button', { name: 'Kontör yükle: BuildingFlow SMS' }));
    const panel = screen.getByLabelText('Yüklenecek kontör').closest('form')!;
    fireEvent.change(within(panel).getByLabelText('Yüklenecek kontör'), { target: { value: '1000' } });
    fireEvent.click(within(panel).getByRole('button', { name: 'Kontörü yükle' }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        'http://hub.test/v1/tenants/11111111-1111-1111-1111-111111111111/sms-accounts/sms-1/credits',
        expect.objectContaining({ method: 'POST', body: JSON.stringify({ kind: 'load', quantity: 1000 }) }),
      ),
    );
  });
});

describe('sms form rules', () => {
  const base: SmsFormState = {
    name: 'SMS', providerType: 'netgsm', senderHeader: 'BLDFLOW', username: 'u', password: 'p', environment: 'production',
    enabled: true, makeDefault: false, lowCreditThreshold: 100, consoleUrl: '',
  };

  it('validates header, credentials and threshold', () => {
    const opts = { creating: true, hasSecret: false, requiresCredentials: true };
    expect(validateSmsForm(base, opts)).toEqual({});
    expect(validateSmsForm({ ...base, senderHeader: 'AB' }, opts).senderHeader).toBe('sms.form.error.header');
    expect(validateSmsForm({ ...base, username: '', password: '' }, opts)).toMatchObject({
      username: 'smtp.form.error.required',
      password: 'smtp.form.error.required',
    });
    expect(validateSmsForm({ ...base, password: '' }, { ...opts, creating: false, hasSecret: true }).password).toBeUndefined();
    expect(validateSmsForm({ ...base, username: '', password: '' }, { ...opts, requiresCredentials: false })).toEqual({});
    expect(validateSmsForm({ ...base, lowCreditThreshold: -1 }, opts).lowCreditThreshold).toBe('sms.form.error.threshold');
  });
});

import type {
  CacheAccount,
  CacheAccountCreate,
  CacheAccountInput,
  CacheCapability,
  CacheConnectionTest,
  ConnectionTest,
  EmailDelivery,
  Me,
  Page,
  ProblemDetails,
  SmtpAccount,
  SmtpAccountCreate,
  SmtpAccountInput,
  SmtpCapability,
} from './types';

export class HubApiError extends Error {
  readonly status: number;
  readonly problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(problem.detail ?? problem.title ?? `HTTP ${problem.status}`);
    this.name = 'HubApiError';
    this.status = problem.status;
    this.problem = problem;
  }

  fieldError(field: string): string | undefined {
    return this.problem.errors?.find((e) => e.field === field)?.message;
  }
}

export interface HubClientOptions {
  baseUrl: string;
  getAccessToken: () => Promise<string | null>;
  /** Yalnız yerel geliştirme: API'nin AIH_AUTH_DEV_MODE ayarıyla birlikte çalışır. */
  devUser?: string;
  fetchImpl?: typeof fetch;
}

export interface ListSmtpParams {
  environment?: string;
  enabled?: boolean;
  providerType?: string;
  q?: string;
  limit?: number;
  cursor?: string | null;
}

type Query = Record<string, string | number | boolean | null | undefined>;

function newIdempotencyKey(): string {
  return `ui-${globalThis.crypto.randomUUID()}`;
}

export function createHubClient(options: HubClientOptions) {
  const base = options.baseUrl.replace(/\/+$/, '');
  const doFetch = options.fetchImpl ?? globalThis.fetch.bind(globalThis);

  async function request<T>(
    method: string,
    path: string,
    init: { body?: unknown; query?: Query; headers?: Record<string, string> } = {},
  ): Promise<{ data: T; etag: string | null }> {
    const url = new URL(base + path, globalThis.location?.origin ?? 'http://localhost');
    for (const [key, value] of Object.entries(init.query ?? {})) {
      if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value));
    }
    const headers: Record<string, string> = { Accept: 'application/json', ...init.headers };
    const token = await options.getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    else if (options.devUser) headers['X-AIH-Dev-User'] = options.devUser;
    if (init.body !== undefined) headers['Content-Type'] = 'application/json';
    const response = await doFetch(url.toString(), {
      method,
      headers,
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
      credentials: 'omit',
    });
    const text = await response.text();
    const payload: unknown = text ? JSON.parse(text) : null;
    if (!response.ok) {
      const problem = (payload as ProblemDetails | null) ?? { status: response.status };
      throw new HubApiError({ ...problem, status: response.status });
    }
    return { data: payload as T, etag: response.headers.get('ETag') };
  }

  const tenantPath = (tenantId: string) => `/v1/tenants/${encodeURIComponent(tenantId)}`;
  const accountPath = (tenantId: string, id: string) =>
    `${tenantPath(tenantId)}/smtp-accounts/${encodeURIComponent(id)}`;
  const cachePath = (tenantId: string, id: string) =>
    `${tenantPath(tenantId)}/cache-accounts/${encodeURIComponent(id)}`;
  const ifMatch = (version: number) => ({ 'If-Match': `W/"${version}"` });

  return {
    me: async () => (await request<Me>('GET', '/v1/me')).data,
    smtpCapabilities: async () => (await request<SmtpCapability[]>('GET', '/v1/provider-types/smtp')).data,
    listSmtpAccounts: async (tenantId: string, params: ListSmtpParams = {}) =>
      (
        await request<Page<SmtpAccount>>('GET', `${tenantPath(tenantId)}/smtp-accounts`, {
          query: params as Query,
        })
      ).data,
    getSmtpAccount: async (tenantId: string, id: string) =>
      (await request<SmtpAccount>('GET', accountPath(tenantId, id))).data,
    createSmtpAccount: async (tenantId: string, body: SmtpAccountCreate) =>
      (await request<SmtpAccount>('POST', `${tenantPath(tenantId)}/smtp-accounts`, { body })).data,
    updateSmtpAccount: async (tenantId: string, id: string, version: number, body: Partial<SmtpAccountInput>) =>
      (await request<SmtpAccount>('PATCH', accountPath(tenantId, id), { body, headers: ifMatch(version) })).data,
    rotateSmtpSecret: async (tenantId: string, id: string, version: number, password: string) =>
      (
        await request<SmtpAccount>('POST', `${accountPath(tenantId, id)}/secret`, {
          body: { password },
          headers: ifMatch(version),
        })
      ).data,
    makeDefaultSmtpAccount: async (tenantId: string, id: string, version: number) =>
      (await request<SmtpAccount>('POST', `${accountPath(tenantId, id)}/make-default`, { headers: ifMatch(version) }))
        .data,
    testSmtpConnection: async (tenantId: string, id: string) =>
      (await request<ConnectionTest>('POST', `${accountPath(tenantId, id)}/test-connection`)).data,
    sendTestEmail: async (tenantId: string, id: string, recipient: string, idempotencyKey = newIdempotencyKey()) =>
      (
        await request<EmailDelivery>('POST', `${accountPath(tenantId, id)}/send-test-email`, {
          body: { recipient, confirm: true },
          headers: { 'Idempotency-Key': idempotencyKey },
        })
      ).data,
    listEmailDeliveries: async (tenantId: string, query: { accountId?: string; status?: string; limit?: number } = {}) =>
      (await request<EmailDelivery[]>('GET', `${tenantPath(tenantId)}/email-deliveries`, { query })).data,
    cacheCapabilities: async () => (await request<CacheCapability[]>('GET', '/v1/provider-types/cache')).data,
    listCacheAccounts: async (tenantId: string, query: { q?: string; limit?: number } = {}) =>
      (await request<Page<CacheAccount>>('GET', `${tenantPath(tenantId)}/cache-accounts`, { query })).data,
    createCacheAccount: async (tenantId: string, body: CacheAccountCreate) =>
      (await request<CacheAccount>('POST', `${tenantPath(tenantId)}/cache-accounts`, { body })).data,
    updateCacheAccount: async (
      tenantId: string,
      id: string,
      version: number,
      body: Partial<CacheAccountInput> & { password?: string },
    ) => (await request<CacheAccount>('PATCH', cachePath(tenantId, id), { body, headers: ifMatch(version) })).data,
    makeDefaultCacheAccount: async (tenantId: string, id: string, version: number) =>
      (await request<CacheAccount>('POST', `${cachePath(tenantId, id)}/make-default`, { headers: ifMatch(version) }))
        .data,
    testCacheConnection: async (tenantId: string, id: string) =>
      (await request<CacheConnectionTest>('POST', `${cachePath(tenantId, id)}/test-connection`)).data,
  };
}

export type HubClient = ReturnType<typeof createHubClient>;

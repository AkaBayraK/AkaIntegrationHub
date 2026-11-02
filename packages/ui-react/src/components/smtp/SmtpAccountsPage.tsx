import { useCallback, useEffect, useState } from 'react';
import type { AccountEnvironment, ConnectionTest, ProviderType, SmtpAccount } from '../../api/types';
import { useAkaIntegration, useTranslation } from '../../context';
import { useHubClient, useHubSession } from '../../session';
import { ConnectionTestResult } from './ConnectionTestResult';
import { SendTestEmailPanel } from './SendTestEmailPanel';
import { Badge, ConfirmPanel, ErrorNotice, formatDate } from './shared';

export const SMTP_BASE_PATH = '/admin/email/providers';

const PROVIDER_LABELS: Record<ProviderType, string> = {
  custom_smtp: 'Custom SMTP',
  microsoft_365: 'Microsoft 365',
  google_workspace: 'Google Workspace',
  amazon_ses: 'Amazon SES',
  mailpit_test: 'Mailpit',
};

type Pending = { kind: 'disable' | 'enable' | 'makeDefault'; account: SmtpAccount } | null;

export function SmtpAccountsPage({ basePath = SMTP_BASE_PATH }: { basePath?: string }) {
  const t = useTranslation();
  const { navigation, locale } = useAkaIntegration();
  const client = useHubClient();
  const session = useHubSession();
  const tenantId = session.me?.tenant.id ?? null;
  const canWrite = session.can('smtp-account:write');
  const canTest = session.can('smtp-account:test');
  const canSend = session.can('smtp-account:send-test');

  const [q, setQ] = useState('');
  const [environment, setEnvironment] = useState<AccountEnvironment | ''>('');
  const [status, setStatus] = useState<'' | 'enabled' | 'disabled'>('');
  const [providerType, setProviderType] = useState<ProviderType | ''>('');
  const [accounts, setAccounts] = useState<SmtpAccount[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<ConnectionTest | null>(null);
  const [sendFor, setSendFor] = useState<SmtpAccount | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!tenantId) return;
    setError(null);
    try {
      const page = await client.listSmtpAccounts(tenantId, {
        q: q.trim() || undefined,
        environment: environment || undefined,
        enabled: status === '' ? undefined : status === 'enabled',
        providerType: providerType || undefined,
        limit: 200,
      });
      setAccounts(page.items);
    } catch (err) {
      setError(err);
    }
  }, [client, tenantId, q, environment, status, providerType]);

  useEffect(() => {
    const handle = setTimeout(() => void load(), 250);
    return () => clearTimeout(handle);
  }, [load]);

  async function runTest(account: SmtpAccount) {
    setBusyId(account.id);
    setTestResult(null);
    try {
      setTestResult(await client.testSmtpConnection(account.tenantId, account.id));
      await load();
    } catch (err) {
      setError(err);
    } finally {
      setBusyId(null);
    }
  }

  async function confirmPending(action: Pending = pending) {
    if (!action) return;
    const { kind, account } = action;
    setBusyId(account.id);
    try {
      if (kind === 'makeDefault') {
        await client.makeDefaultSmtpAccount(account.tenantId, account.id, account.version);
        setToast(t('smtp.toast.defaultChanged'));
      } else {
        await client.updateSmtpAccount(account.tenantId, account.id, account.version, { enabled: kind === 'enable' });
        setToast(t('smtp.toast.statusChanged'));
      }
      setPending(null);
      await load();
    } catch (err) {
      setError(err);
    } finally {
      setBusyId(null);
    }
  }

  if (session.loading) return <p role="status">{t('common.loading')}</p>;
  if (session.error) return <ErrorNotice error={session.error} onRetry={session.reload} />;

  const filtered = Boolean(q || environment || status || providerType);

  return (
    <div className="aih-page">
      <div className="aih-row aih-row--between">
        <div>
          <h1>{t('smtp.title')}</h1>
          <p className="aih-muted">{t('smtp.description')}</p>
        </div>
        {canWrite && (
          <button
            type="button"
            className="aih-button aih-button--primary"
            onClick={() => navigation.navigate(`${basePath}/new`)}
          >
            {t('smtp.new')}
          </button>
        )}
      </div>

      <div className="aih-filters" role="search">
        <label className="aih-field">
          <span className="aih-visually-hidden">{t('smtp.search')}</span>
          <input
            className="aih-input"
            type="search"
            placeholder={t('smtp.search')}
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
        <label className="aih-field">
          <span>{t('smtp.filter.environment')}</span>
          <select className="aih-select" value={environment} onChange={(e) => setEnvironment(e.target.value as AccountEnvironment | '')}>
            <option value="">{t('common.all')}</option>
            <option value="test">{t('smtp.env.test')}</option>
            <option value="production">{t('smtp.env.production')}</option>
          </select>
        </label>
        <label className="aih-field">
          <span>{t('smtp.filter.status')}</span>
          <select className="aih-select" value={status} onChange={(e) => setStatus(e.target.value as '' | 'enabled' | 'disabled')}>
            <option value="">{t('common.all')}</option>
            <option value="enabled">{t('smtp.status.enabled')}</option>
            <option value="disabled">{t('smtp.status.disabled')}</option>
          </select>
        </label>
        <label className="aih-field">
          <span>{t('smtp.filter.provider')}</span>
          <select className="aih-select" value={providerType} onChange={(e) => setProviderType(e.target.value as ProviderType | '')}>
            <option value="">{t('common.all')}</option>
            {(Object.keys(PROVIDER_LABELS) as ProviderType[]).map((type) => (
              <option key={type} value={type}>
                {PROVIDER_LABELS[type]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {toast && (
        <p className="aih-alert aih-alert--success" role="status">
          {toast}
        </p>
      )}
      {error !== null && <ErrorNotice error={error} onRetry={() => void load()} />}
      {pending && (
        <ConfirmPanel
          message={pending.kind === 'makeDefault' ? 'smtp.confirm.makeDefault' : 'smtp.confirm.disable'}
          onConfirm={() => void confirmPending()}
          onCancel={() => setPending(null)}
          busy={busyId === pending.account.id}
        />
      )}
      {testResult && <ConnectionTestResult result={testResult} onClose={() => setTestResult(null)} />}
      {sendFor && (
        <SendTestEmailPanel account={sendFor} defaultRecipient={session.me?.email} onClose={() => setSendFor(null)} />
      )}

      {accounts === null && error === null ? (
        <p role="status">{t('common.loading')}</p>
      ) : accounts && accounts.length === 0 ? (
        <p className="aih-card aih-muted">{filtered ? t('smtp.emptyFiltered') : t('smtp.empty')}</p>
      ) : accounts ? (
        <div className="aih-table-wrap">
          <table className="aih-table">
            <caption className="aih-visually-hidden">{t('smtp.title')}</caption>
            <thead>
              <tr>
                <th scope="col">{t('smtp.col.name')}</th>
                <th scope="col">{t('smtp.col.provider')}</th>
                <th scope="col">{t('smtp.col.host')}</th>
                <th scope="col">{t('smtp.col.sender')}</th>
                <th scope="col">{t('smtp.col.environment')}</th>
                <th scope="col">{t('smtp.col.lastTest')}</th>
                <th scope="col">{t('smtp.col.lastSend')}</th>
                <th scope="col">{t('smtp.col.status')}</th>
                <th scope="col">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.id}>
                  <th scope="row">
                    {account.name} {account.isDefault && <Badge tone="accent">{t('smtp.default')}</Badge>}
                  </th>
                  <td>{PROVIDER_LABELS[account.providerType]}</td>
                  <td>
                    <code>
                      {account.host}:{account.port}
                    </code>
                  </td>
                  <td>{account.senderAddress}</td>
                  <td>{t(account.environment === 'production' ? 'smtp.env.production' : 'smtp.env.test')}</td>
                  <td>
                    {account.lastTestOutcome ? (
                      <Badge tone={account.lastTestOutcome === 'passed' ? 'success' : 'danger'}>
                        {t(account.lastTestOutcome === 'passed' ? 'smtp.test.passed' : 'smtp.test.failed')}
                      </Badge>
                    ) : (
                      <span className="aih-muted">{t('smtp.never')}</span>
                    )}{' '}
                    <span className="aih-muted">{formatDate(account.lastTestAt, locale.locale)}</span>
                  </td>
                  <td>{formatDate(account.lastSuccessSendAt, locale.locale) ?? <span className="aih-muted">{t('smtp.never')}</span>}</td>
                  <td>
                    <Badge tone={account.enabled ? 'success' : 'neutral'}>
                      {t(account.enabled ? 'smtp.status.enabled' : 'smtp.status.disabled')}
                    </Badge>
                  </td>
                  <td>
                    <div className="aih-row aih-table-actions">
                      {canWrite && (
                        <button
                          type="button"
                          className="aih-button aih-button--ghost aih-button--sm"
                          onClick={() => navigation.navigate(`${basePath}/${account.id}/edit`)}
                          aria-label={`${t('smtp.action.edit')}: ${account.name}`}
                        >
                          {t('smtp.action.edit')}
                        </button>
                      )}
                      {canTest && (
                        <button
                          type="button"
                          className="aih-button aih-button--ghost aih-button--sm"
                          onClick={() => void runTest(account)}
                          disabled={busyId === account.id}
                          aria-label={`${t('smtp.action.test')}: ${account.name}`}
                        >
                          {busyId === account.id ? t('common.loading') : t('smtp.action.test')}
                        </button>
                      )}
                      {canSend && account.enabled && (
                        <button
                          type="button"
                          className="aih-button aih-button--ghost aih-button--sm"
                          onClick={() => setSendFor(account)}
                          aria-label={`${t('smtp.action.sendTest')}: ${account.name}`}
                        >
                          {t('smtp.action.sendTest')}
                        </button>
                      )}
                      {canWrite && account.enabled && !account.isDefault && (
                        <button
                          type="button"
                          className="aih-button aih-button--ghost aih-button--sm"
                          onClick={() => setPending({ kind: 'makeDefault', account })}
                          aria-label={`${t('smtp.action.makeDefault')}: ${account.name}`}
                        >
                          {t('smtp.action.makeDefault')}
                        </button>
                      )}
                      {canWrite && (
                        <button
                          type="button"
                          className="aih-button aih-button--ghost aih-button--sm"
                          onClick={() =>
                            account.enabled
                              ? setPending({ kind: 'disable', account })
                              : void confirmPending({ kind: 'enable', account })
                          }
                          aria-label={`${t(account.enabled ? 'smtp.action.disable' : 'smtp.action.enable')}: ${account.name}`}
                        >
                          {t(account.enabled ? 'smtp.action.disable' : 'smtp.action.enable')}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}

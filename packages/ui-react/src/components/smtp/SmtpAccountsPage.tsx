import { useCallback, useEffect, useState } from 'react';
import type { AccountEnvironment, ConnectionTest, ProviderType, SmtpAccount } from '../../api/types';
import { HealthBadge } from '../integrations/IntegrationsHome';
import { IntegrationIcon, smtpHealth } from '../integrations/catalog';
import { useAkaIntegration, useTranslation } from '../../context';
import { useHubClient, useHubSession } from '../../session';
import { ConnectionTestResult } from './ConnectionTestResult';
import { SendTestEmailPanel } from './SendTestEmailPanel';
import { PROVIDER_LABELS } from './providers';
import { Badge, ConfirmPanel, ErrorNotice, formatDate } from './shared';

export const SMTP_BASE_PATH = '/admin/email/providers';

type Pending = { kind: 'disable' | 'enable' | 'makeDefault'; account: SmtpAccount } | null;

export const EMAIL_DELIVERIES_PATH = '/admin/email/deliveries';

const TLS_KEYS = {
  starttls: 'smtp.form.tls.starttls',
  implicit: 'smtp.form.tls.implicit',
  none: 'smtp.form.tls.none',
} as const;

const AUTH_KEYS = {
  smtp_auth: 'smtp.form.auth.smtp_auth',
  oauth2: 'smtp.form.auth.oauth2',
  none: 'smtp.form.auth.none',
} as const;

function initials(name: string): string {
  return name.trim().charAt(0).toLocaleUpperCase('tr-TR') || '?';
}

export function SmtpAccountsPage({
  basePath = SMTP_BASE_PATH,
  homePath = '/',
  deliveriesPath = EMAIL_DELIVERIES_PATH,
  initialAccountId,
}: {
  basePath?: string;
  /** Entegrasyonlar ana sayfası. */
  homePath?: string;
  deliveriesPath?: string;
  /** Ana sayfadaki bir bağlantı kutusundan gelindiğinde seçili açılacak hesap. */
  initialAccountId?: string | null;
}) {
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
  const [selectedId, setSelectedId] = useState<string | null>(initialAccountId ?? null);

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
  const list = accounts ?? [];
  const selected = list.find((a) => a.id === selectedId) ?? list.find((a) => a.isDefault) ?? list[0] ?? null;
  const activeCount = list.filter((a) => a.enabled).length;
  const passedCount = list.filter((a) => smtpHealth(a) === 'healthy').length;
  const attentionCount = list.filter((a) => smtpHealth(a) === 'failed').length;
  const defaultAccount = list.find((a) => a.isDefault && a.enabled);

  return (
    <div className="aih-page">
      <a
        className="aih-back"
        href={homePath}
        onClick={(event) => {
          event.preventDefault();
          navigation.navigate(homePath);
        }}
      >
        ← {t('home.title')}
      </a>
      <div className="aih-row aih-row--between">
        <div className="aih-row aih-row--start">
          <span className="aih-type-icon aih-type-icon--lg aih-tile--smtp">
            <IntegrationIcon type="smtp" size={26} />
          </span>
          <div>
            <h1>{t('smtp.title')}</h1>
            <p className="aih-muted">{t('smtp.description')}</p>
          </div>
        </div>
        <div className="aih-row aih-row--wrap">
          <button type="button" className="aih-button aih-button--ghost" onClick={() => navigation.navigate(deliveriesPath)}>
            {t('nav.emailDeliveries')}
          </button>
          {canWrite && (
            <button
              type="button"
              className="aih-button aih-button--primary"
              onClick={() => navigation.navigate(`${basePath}/new`)}
            >
              + {t('smtp.new')}
            </button>
          )}
        </div>
      </div>

      {accounts && (
        <ul className="aih-kpis" aria-label={t('smtp.kpi.label')}>
          <li className="aih-kpi">
            <span>{t('smtp.kpi.active')}</span>
            <strong>
              {activeCount}/{list.length}
            </strong>
          </li>
          <li className="aih-kpi">
            <span>{t('smtp.kpi.default')}</span>
            <strong className="aih-kpi__text">{defaultAccount?.name ?? '–'}</strong>
          </li>
          <li className="aih-kpi">
            <span>{t('smtp.kpi.passed')}</span>
            <strong>{passedCount}</strong>
          </li>
          <li className={`aih-kpi${attentionCount > 0 ? ' aih-kpi--danger' : ''}`}>
            <span>{t('smtp.kpi.attention')}</span>
            <strong>{attentionCount}</strong>
          </li>
        </ul>
      )}

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
      {accounts === null && error === null ? (
        <p role="status">{t('common.loading')}</p>
      ) : accounts && accounts.length === 0 ? (
        <p className="aih-card aih-muted">{filtered ? t('smtp.emptyFiltered') : t('smtp.empty')}</p>
      ) : accounts ? (
        <div className="aih-split">
          <ul className="aih-split__list" aria-label={t('smtp.listLabel')}>
            {accounts.map((account) => {
              const health = smtpHealth(account);
              const isSelected = selected?.id === account.id;
              return (
                <li key={account.id}>
                  <button
                    type="button"
                    className={`aih-list-item${isSelected ? ' aih-list-item--selected' : ''}`}
                    aria-pressed={isSelected}
                    onClick={() => setSelectedId(account.id)}
                  >
                    <span className="aih-avatar" aria-hidden="true">
                      {initials(account.name)}
                    </span>
                    <span className="aih-list-item__body">
                      <span className="aih-list-item__name">{account.name}</span>
                      <span className="aih-muted">
                        {PROVIDER_LABELS[account.providerType]}
                        {account.isDefault ? ` · ${t('smtp.default')}` : ''}
                      </span>
                    </span>
                    <HealthBadge health={health} />
                  </button>
                </li>
              );
            })}
            {canWrite && (
              <li>
                <button
                  type="button"
                  className="aih-list-item aih-list-item--add"
                  onClick={() => navigation.navigate(`${basePath}/new`)}
                >
                  + {t('smtp.form.createTitle')}
                </button>
              </li>
            )}
          </ul>

          {selected && (
            <section className="aih-split__detail" aria-label={selected.name}>
              <div className="aih-detail-card aih-detail-card--head">
                <span className="aih-avatar aih-avatar--lg" aria-hidden="true">
                  {initials(selected.name)}
                </span>
                <div className="aih-detail-card__title">
                  <h2>
                    {selected.name} {selected.isDefault && <Badge tone="accent">{t('smtp.default')}</Badge>}
                  </h2>
                  <p className="aih-muted">
                    {selected.senderAddress} · <code>{selected.host}:{selected.port}</code> · {t(TLS_KEYS[selected.tlsMode])}
                  </p>
                </div>
                <HealthBadge health={smtpHealth(selected)} />
              </div>

              <div className="aih-detail-actions">
                {canWrite && (
                  <button
                    type="button"
                    className="aih-button aih-button--ghost"
                    onClick={() => navigation.navigate(`${basePath}/${selected.id}/edit`)}
                    aria-label={`${t('smtp.action.edit')}: ${selected.name}`}
                  >
                    {t('smtp.action.edit')}
                  </button>
                )}
                {canWrite && selected.enabled && !selected.isDefault && (
                  <button
                    type="button"
                    className="aih-button aih-button--ghost"
                    onClick={() => setPending({ kind: 'makeDefault', account: selected })}
                    aria-label={`${t('smtp.action.makeDefault')}: ${selected.name}`}
                  >
                    {t('smtp.action.makeDefault')}
                  </button>
                )}
                {canWrite && (
                  <button
                    type="button"
                    className="aih-button aih-button--ghost"
                    onClick={() =>
                      selected.enabled
                        ? setPending({ kind: 'disable', account: selected })
                        : void confirmPending({ kind: 'enable', account: selected })
                    }
                    aria-label={`${t(selected.enabled ? 'smtp.action.disable' : 'smtp.action.enable')}: ${selected.name}`}
                  >
                    {t(selected.enabled ? 'smtp.action.disable' : 'smtp.action.enable')}
                  </button>
                )}
              </div>

              <div className="aih-detail-grid">
                <div className="aih-detail-card">
                  <h3>{t('smtp.detail.connection')}</h3>
                  <dl className="aih-props">
                    <div>
                      <dt>{t('smtp.col.provider')}</dt>
                      <dd>{PROVIDER_LABELS[selected.providerType]}</dd>
                    </div>
                    <div>
                      <dt>{t('smtp.col.environment')}</dt>
                      <dd>{t(selected.environment === 'production' ? 'smtp.env.production' : 'smtp.env.test')}</dd>
                    </div>
                    <div>
                      <dt>{t('smtp.form.authMode')}</dt>
                      <dd>{t(AUTH_KEYS[selected.authMode])}</dd>
                    </div>
                    <div>
                      <dt>{t('smtp.col.status')}</dt>
                      <dd>{t(selected.enabled ? 'smtp.status.enabled' : 'smtp.status.disabled')}</dd>
                    </div>
                    <div>
                      <dt>{t('smtp.col.lastSend')}</dt>
                      <dd>{formatDate(selected.lastSuccessSendAt, locale.locale) ?? t('smtp.never')}</dd>
                    </div>
                  </dl>
                </div>

                <div className="aih-detail-card">
                  <div className="aih-row aih-row--between">
                    <h3>{t('smtp.col.lastTest')}</h3>
                    <span className="aih-muted">{formatDate(selected.lastTestAt, locale.locale) ?? t('smtp.never')}</span>
                  </div>
                  {testResult && testResult.accountId === selected.id ? (
                    <ConnectionTestResult result={testResult} onClose={() => setTestResult(null)} />
                  ) : (
                    <p className="aih-muted">
                      {selected.lastTestOutcome
                        ? t(selected.lastTestOutcome === 'passed' ? 'smtp.test.passed' : 'smtp.test.failed')
                        : t('smtp.detail.noTest')}
                    </p>
                  )}
                  {canTest && (
                    <button
                      type="button"
                      className="aih-button aih-button--ghost aih-detail-card__cta"
                      onClick={() => void runTest(selected)}
                      disabled={busyId === selected.id}
                      aria-label={`${t('smtp.action.test')}: ${selected.name}`}
                    >
                      {busyId === selected.id ? t('common.loading') : t('smtp.action.test')}
                    </button>
                  )}
                </div>

                {canSend && selected.enabled && (
                  <div className="aih-detail-card">
                    {sendFor?.id === selected.id ? (
                      <SendTestEmailPanel
                        account={selected}
                        defaultRecipient={session.me?.email}
                        onClose={() => setSendFor(null)}
                      />
                    ) : (
                      <>
                    <h3>{t('smtp.sendTest.title')}</h3>
                    <p className="aih-muted">{t('smtp.detail.sendHint')}</p>
                    <button
                      type="button"
                      className="aih-button aih-button--primary aih-detail-card__cta"
                      onClick={() => setSendFor(selected)}
                      aria-label={`${t('smtp.action.sendTest')}: ${selected.name}`}
                    >
                      {t('smtp.action.sendTest')}
                    </button>
                      </>
                    )}
                  </div>
                )}
              </div>
            </section>
          )}
        </div>
      ) : null}
    </div>
  );
}

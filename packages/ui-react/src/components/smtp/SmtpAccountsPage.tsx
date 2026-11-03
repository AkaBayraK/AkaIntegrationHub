import { useCallback, useEffect, useState, type ReactNode } from 'react';
import type { AccountEnvironment, ConnectionTest, ProviderType, SmtpAccount } from '../../api/types';
import { useAkaIntegration, useTranslation } from '../../context';
import { useHubClient, useHubSession } from '../../session';
import { ConnectionTestResult } from './ConnectionTestResult';
import { SendTestEmailPanel } from './SendTestEmailPanel';
import {
  accountHealth,
  Badge,
  ConfirmPanel,
  ErrorNotice,
  formatDate,
  HEALTH_LABELS,
  HEALTH_TONES,
  Kpi,
  PROVIDER_LABELS,
  ProviderMark,
  SMTP_BASE_PATH,
  StatusPill,
  TypeMark,
} from './shared';

export { SMTP_BASE_PATH } from './shared';

type Pending = { kind: 'disable' | 'enable' | 'makeDefault'; account: SmtpAccount } | null;
type Translate = ReturnType<typeof useTranslation>;

export function SmtpAccountsPage({ basePath = SMTP_BASE_PATH, homePath = '/' }: { basePath?: string; homePath?: string }) {
  const t = useTranslation();
  const { navigation } = useAkaIntegration();
  const client = useHubClient();
  const session = useHubSession();
  const tenantId = session.me?.tenant.id ?? null;
  const canWrite = session.can('smtp-account:write');

  const [q, setQ] = useState('');
  const [environment, setEnvironment] = useState<AccountEnvironment | ''>('');
  const [status, setStatus] = useState<'' | 'enabled' | 'disabled'>('');
  const [providerType, setProviderType] = useState<ProviderType | ''>('');
  const [accounts, setAccounts] = useState<SmtpAccount[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
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
  const selected = accounts?.find((a) => a.id === selectedId) ?? accounts?.[0] ?? null;

  return (
    <div className="aih-page">
      <nav className="aih-crumb" aria-label={t('hub.back')}>
        <a
          href={homePath}
          onClick={(event) => {
            event.preventDefault();
            navigation.navigate(homePath);
          }}
        >
          ← {t('hub.back')}
        </a>
        <span aria-hidden="true"> / </span>
        <span>{t('hub.type.email.name')}</span>
      </nav>

      <div className="aih-row aih-row--between">
        <div className="aih-row aih-page-title">
          <TypeMark type="email" />
          <div>
            <h1>{t('smtp.title')}</h1>
            <p className="aih-muted">{t('smtp.description')}</p>
          </div>
        </div>
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

      {accounts && accounts.length > 0 && <SmtpKpis accounts={accounts} t={t} />}

      <div className="aih-filters" role="search">
        <label className="aih-field aih-field--grow">
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
      {sendFor && (
        <SendTestEmailPanel account={sendFor} defaultRecipient={session.me?.email} onClose={() => setSendFor(null)} />
      )}

      {accounts === null && error === null ? (
        <p role="status">{t('common.loading')}</p>
      ) : accounts && accounts.length === 0 ? (
        <p className="aih-card aih-muted">{filtered ? t('smtp.emptyFiltered') : t('smtp.empty')}</p>
      ) : accounts && selected ? (
        <div className="aih-split">
          <AccountList
            accounts={accounts}
            selectedId={selected.id}
            onSelect={(id) => {
              setSelectedId(id);
              setTestResult(null);
            }}
            onCreate={canWrite ? () => navigation.navigate(`${basePath}/new`) : undefined}
            t={t}
          />
          <AccountDetail
            account={selected}
            basePath={basePath}
            busy={busyId === selected.id}
            testResult={testResult?.accountId === selected.id ? testResult : null}
            onCloseTest={() => setTestResult(null)}
            onTest={() => void runTest(selected)}
            onSendTest={() => setSendFor(selected)}
            onMakeDefault={() => setPending({ kind: 'makeDefault', account: selected })}
            onToggle={() =>
              selected.enabled
                ? setPending({ kind: 'disable', account: selected })
                : void confirmPending({ kind: 'enable', account: selected })
            }
          />
        </div>
      ) : null}
    </div>
  );
}

function SmtpKpis({ accounts, t }: { accounts: SmtpAccount[]; t: Translate }) {
  const active = accounts.filter((a) => a.enabled).length;
  const tested = accounts.filter((a) => a.lastTestOutcome !== null);
  const passed = tested.filter((a) => a.lastTestOutcome === 'passed').length;
  const failing = accounts.filter((a) => accountHealth(a) === 'failing');
  const defaults = accounts.filter((a) => a.isDefault).map((a) => a.name);
  return (
    <div className="aih-kpis">
      <Kpi label={t('smtp.kpi.active')} value={`${active} / ${accounts.length}`} />
      <Kpi label={t('smtp.kpi.default')} value={defaults[0] ?? t('smtp.kpi.none')} hint={defaults.slice(1).join(', ') || undefined} />
      <Kpi label={t('smtp.kpi.tested')} value={`${passed} / ${tested.length}`} />
      <Kpi
        label={t('smtp.kpi.attention')}
        value={failing.length}
        hint={failing.length ? failing.map((a) => a.name).join(', ') : t('smtp.kpi.allGood')}
        tone={failing.length ? 'danger' : 'success'}
      />
    </div>
  );
}

function AccountList({
  accounts,
  selectedId,
  onSelect,
  onCreate,
  t,
}: {
  accounts: SmtpAccount[];
  selectedId: string;
  onSelect: (id: string) => void;
  onCreate?: () => void;
  t: Translate;
}) {
  return (
    <div className="aih-surface aih-list">
      <ul aria-label={t('smtp.list.label')}>
        {accounts.map((account) => {
          const health = accountHealth(account);
          return (
            <li key={account.id}>
              <button
                type="button"
                className={account.id === selectedId ? 'aih-list__item aih-list__item--active' : 'aih-list__item'}
                aria-current={account.id === selectedId ? 'true' : undefined}
                onClick={() => onSelect(account.id)}
              >
                <ProviderMark providerType={account.providerType} size="sm" />
                <span className="aih-list__text">
                  <span className="aih-list__name">{account.name}</span>
                  <span className="aih-list__sub">{account.senderAddress}</span>
                </span>
                <span className={`aih-dot aih-dot--${HEALTH_TONES[health]}`} title={t(HEALTH_LABELS[health])} />
              </button>
            </li>
          );
        })}
      </ul>
      {onCreate && (
        <button type="button" className="aih-add-row" onClick={onCreate}>
          + {t('smtp.new')}
        </button>
      )}
    </div>
  );
}

function AccountDetail({
  account,
  basePath,
  busy,
  testResult,
  onCloseTest,
  onTest,
  onSendTest,
  onMakeDefault,
  onToggle,
}: {
  account: SmtpAccount;
  basePath: string;
  busy: boolean;
  testResult: ConnectionTest | null;
  onCloseTest: () => void;
  onTest: () => void;
  onSendTest: () => void;
  onMakeDefault: () => void;
  onToggle: () => void;
}) {
  const t = useTranslation();
  const { navigation, locale } = useAkaIntegration();
  const session = useHubSession();
  const canWrite = session.can('smtp-account:write');
  const canTest = session.can('smtp-account:test');
  const canSend = session.can('smtp-account:send-test');
  const health = accountHealth(account);
  const headingId = `aih-account-${account.id}`;
  const tls = t(`smtp.form.tls.${account.tlsMode}` as const);
  const secret = t(account.hasSecret ? 'smtp.detail.secretStored' : 'smtp.detail.noSecret');

  return (
    <section className="aih-surface aih-detail" aria-labelledby={headingId}>
      <header className="aih-detail__head">
        <ProviderMark providerType={account.providerType} />
        <div className="aih-detail__title">
          <h2 id={headingId}>{account.name}</h2>
          <p className="aih-muted">
            {PROVIDER_LABELS[account.providerType]} ·{' '}
            {t(account.environment === 'production' ? 'smtp.env.production' : 'smtp.env.test')}
          </p>
        </div>
        <div className="aih-row aih-row--wrap">
          {account.isDefault && <Badge tone="accent">{t('smtp.default')}</Badge>}
          <StatusPill tone={HEALTH_TONES[health]}>{t(HEALTH_LABELS[health])}</StatusPill>
        </div>
      </header>

      <dl className="aih-facts">
        <Fact label={t('smtp.col.sender')} value={account.senderAddress} />
        <Fact label={t('smtp.col.host')} value={<code>{`${account.host}:${account.port}`}</code>} />
        <Fact label={t('smtp.detail.security')} value={`${tls} · ${secret}`} />
        <Fact label={t('smtp.detail.priority')} value={account.priority} />
        <Fact label={t('smtp.detail.timeout')} value={`${account.timeoutSeconds} ${t('smtp.detail.seconds')}`} />
        <Fact
          label={t('smtp.detail.rateLimit')}
          value={
            account.rateLimitPerMinute ? `${account.rateLimitPerMinute} ${t('smtp.detail.perMinute')}` : t('smtp.detail.unlimited')
          }
        />
        <Fact label={t('smtp.col.lastSend')} value={formatDate(account.lastSuccessSendAt, locale.locale) ?? t('smtp.never')} />
      </dl>

      <div className="aih-detail__test">
        <h3>
          {t('smtp.detail.lastTest')}
          {account.lastTestAt && <span className="aih-muted"> · {formatDate(account.lastTestAt, locale.locale)}</span>}
        </h3>
        {testResult ? (
          <ConnectionTestResult result={testResult} onClose={onCloseTest} />
        ) : account.lastTestOutcome ? (
          <Badge tone={account.lastTestOutcome === 'passed' ? 'success' : 'danger'}>
            {t(account.lastTestOutcome === 'passed' ? 'smtp.test.passed' : 'smtp.test.failed')}
          </Badge>
        ) : (
          <p className="aih-muted">{t('smtp.detail.notTested')}</p>
        )}
      </div>

      <div className="aih-row aih-row--wrap">
        {canTest && (
          <button
            type="button"
            className="aih-button aih-button--primary"
            onClick={onTest}
            disabled={busy}
            aria-label={`${t('smtp.action.test')}: ${account.name}`}
          >
            {busy ? t('common.loading') : t('smtp.action.test')}
          </button>
        )}
        {canSend && account.enabled && (
          <button
            type="button"
            className="aih-button aih-button--ghost"
            onClick={onSendTest}
            aria-label={`${t('smtp.action.sendTest')}: ${account.name}`}
          >
            {t('smtp.action.sendTest')}
          </button>
        )}
        {canWrite && (
          <button
            type="button"
            className="aih-button aih-button--ghost"
            onClick={() => navigation.navigate(`${basePath}/${account.id}/edit`)}
            aria-label={`${t('smtp.action.edit')}: ${account.name}`}
          >
            {t('smtp.action.edit')}
          </button>
        )}
        {canWrite && account.enabled && !account.isDefault && (
          <button
            type="button"
            className="aih-button aih-button--ghost"
            onClick={onMakeDefault}
            aria-label={`${t('smtp.action.makeDefault')}: ${account.name}`}
          >
            {t('smtp.action.makeDefault')}
          </button>
        )}
        {canWrite && (
          <button
            type="button"
            className="aih-button aih-button--ghost"
            onClick={onToggle}
            aria-label={`${t(account.enabled ? 'smtp.action.disable' : 'smtp.action.enable')}: ${account.name}`}
          >
            {t(account.enabled ? 'smtp.action.disable' : 'smtp.action.enable')}
          </button>
        )}
      </div>
    </section>
  );
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="aih-fact">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

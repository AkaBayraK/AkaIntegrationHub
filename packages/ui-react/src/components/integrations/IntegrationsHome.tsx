import { useCallback, useEffect, useState, type ReactNode } from 'react';
import type { SmtpAccount } from '../../api/types';
import { useAkaIntegration, useTranslation } from '../../context';
import { useHubClient, useHubSession } from '../../session';
import {
  accountHealth,
  ErrorNotice,
  formatDate,
  HEALTH_LABELS,
  HEALTH_TONES,
  PROVIDER_LABELS,
  ProviderMark,
  StatusPill,
  TypeMark,
} from '../smtp/shared';
import { SortableGrid, useCardLayout } from '../layout/SortableGrid';
import { INTEGRATION_TYPES, type IntegrationType, type IntegrationTypeId } from './catalog';

type Filter = 'all' | 'problems' | 'production' | 'test';

const FILTERS: readonly Filter[] = ['all', 'problems', 'production', 'test'];
const TYPE_IDS: readonly string[] = INTEGRATION_TYPES.map((type) => type.id);

export function IntegrationsHome({ headerExtra }: { headerExtra?: ReactNode }) {
  const t = useTranslation();
  const client = useHubClient();
  const session = useHubSession();
  const tenantId = session.me?.tenant.id ?? null;
  const canReadEmail = session.can('smtp-account:read');
  const [smtpAccounts, setSmtpAccounts] = useState<SmtpAccount[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [editing, setEditing] = useState(false);
  const subject = session.me?.subject ?? null;
  const typeLayout = useCardLayout('hub-types', subject, TYPE_IDS);
  const accountLayout = useCardLayout('hub-defined', subject, (smtpAccounts ?? []).map((account) => account.id));

  const load = useCallback(async () => {
    if (!tenantId || !canReadEmail) {
      setSmtpAccounts([]);
      return;
    }
    setError(null);
    try {
      setSmtpAccounts((await client.listSmtpAccounts(tenantId, { limit: 200 })).items);
    } catch (err) {
      setError(err);
    }
  }, [client, tenantId, canReadEmail]);

  useEffect(() => {
    void load();
  }, [load]);

  if (session.loading) return <p role="status">{t('common.loading')}</p>;
  if (session.error) return <ErrorNotice error={session.error} onRetry={session.reload} />;

  const accounts = smtpAccounts ?? [];
  const counts: Partial<Record<IntegrationTypeId, number>> = { email: accounts.length };
  const problems = accounts.filter((a) => accountHealth(a) === 'failing').length;
  const healthy = accounts.filter((a) => accountHealth(a) === 'healthy').length;
  const visible = accounts.filter((a) => matchesFilter(a, filter));

  return (
    <div className="aih-page">
      <div className="aih-row aih-row--between">
        <div>
          <h1>{t('hub.title')}</h1>
          <p className="aih-muted">
            {session.me?.tenant.name} · {t('hub.description')}
          </p>
        </div>
        <div className="aih-row aih-row--wrap">
          {headerExtra}
          {accounts.length > 0 && (
            <StatusPill tone="success">
              {healthy} / {accounts.length} {t('hub.summary.healthy')}
            </StatusPill>
          )}
          {problems > 0 && (
            <StatusPill tone="danger">
              {problems} {t('hub.summary.problems')}
            </StatusPill>
          )}
          {editing && !(typeLayout.isDefault && accountLayout.isDefault) && (
            <button
              type="button"
              className="aih-button aih-button--ghost aih-button--sm"
              onClick={() => {
                typeLayout.reset();
                accountLayout.reset();
              }}
            >
              {t('layout.reset')}
            </button>
          )}
          <button
            type="button"
            className={editing ? 'aih-button aih-button--primary aih-button--sm' : 'aih-button aih-button--ghost aih-button--sm'}
            aria-pressed={editing}
            onClick={() => setEditing((value) => !value)}
          >
            {editing ? t('layout.done') : t('layout.edit')}
          </button>
        </div>
      </div>
      {editing && <p className="aih-notice">{t('layout.editHint')}</p>}

      <section aria-labelledby="aih-hub-types" className="aih-section">
        <div className="aih-section__head">
          <h2 id="aih-hub-types">{t('hub.types.title')}</h2>
          <span className="aih-muted">{t('hub.types.hint')}</span>
        </div>
        <SortableGrid
          state={typeLayout}
          editing={editing}
          items={INTEGRATION_TYPES.map((type) => ({
            id: type.id,
            title: t(type.nameKey),
            node: <TypeTile type={type} count={counts[type.id] ?? 0} />,
          }))}
        />
      </section>

      <section aria-labelledby="aih-hub-defined" className="aih-section">
        <div className="aih-section__head">
          <h2 id="aih-hub-defined">
            {t('hub.defined.title')} <span className="aih-muted">· {accounts.length}</span>
          </h2>
          <div className="aih-tabs" role="group" aria-label={t('hub.defined.title')}>
            {FILTERS.map((value) => (
              <button
                key={value}
                type="button"
                className={value === filter ? 'aih-tab aih-tab--active' : 'aih-tab'}
                aria-pressed={value === filter}
                onClick={() => setFilter(value)}
              >
                {filterLabel(value, t)}
                {value === 'problems' && problems > 0 ? ` · ${problems}` : ''}
              </button>
            ))}
          </div>
        </div>
        {error !== null && <ErrorNotice error={error} onRetry={() => void load()} />}
        {smtpAccounts === null && error === null ? (
          <p role="status">{t('common.loading')}</p>
        ) : visible.length === 0 ? (
          <p className="aih-surface aih-empty aih-muted">
            {accounts.length === 0 ? t('hub.defined.empty') : t('hub.defined.emptyFiltered')}
          </p>
        ) : (
          <SortableGrid
            state={accountLayout}
            editing={editing}
            items={visible.map((account) => ({
              id: account.id,
              title: account.name,
              node: <EmailIntegrationCard account={account} />,
            }))}
          />
        )}
      </section>
    </div>
  );
}

function TypeTile({ type, count }: { type: IntegrationType; count: number }) {
  const t = useTranslation();
  const { navigation } = useAkaIntegration();
  const session = useHubSession();
  const name = t(type.nameKey);
  const available = type.basePath !== null;
  const canAdd = available && type.id === 'email' && session.can('smtp-account:write');

  if (!available) {
    return (
      <div className="aih-type aih-type--soon" aria-disabled="true">
        <div className="aih-type__head">
          <TypeMark symbol={type.symbol} type={type.id} />
          <span>
            <span className="aih-type__name">{name}</span>
            <span className="aih-type__desc">{t(type.descriptionKey)}</span>
          </span>
        </div>
        <div className="aih-type__foot">
          <StatusPill tone="neutral">{t('hub.soon')}</StatusPill>
        </div>
      </div>
    );
  }

  return (
    <div className="aih-type">
      <a
        className="aih-type__head aih-type__link"
        href={type.basePath ?? undefined}
        onClick={(event) => {
          event.preventDefault();
          if (type.basePath) navigation.navigate(type.basePath);
        }}
      >
        <TypeMark symbol={type.symbol} type={type.id} />
        <span>
          <span className="aih-type__name">{name}</span>
          <span className="aih-type__desc">{t(type.descriptionKey)}</span>
        </span>
      </a>
      <div className="aih-type__foot">
        <span>
          <strong className="aih-type__count">{count}</strong> {t('hub.count.defined')}
        </span>
        {canAdd && (
          <button
            type="button"
            className="aih-button aih-button--primary aih-button--sm"
            onClick={() => navigation.navigate(`${type.basePath}/new`)}
            aria-label={`${t('hub.add')}: ${name}`}
          >
            + {t('hub.add')}
          </button>
        )}
      </div>
    </div>
  );
}

function EmailIntegrationCard({ account }: { account: SmtpAccount }) {
  const t = useTranslation();
  const { navigation, locale } = useAkaIntegration();
  const health = accountHealth(account);
  const emailType = INTEGRATION_TYPES.find((type) => type.id === 'email');
  const basePath = emailType?.basePath ?? '';
  return (
    <article className={health === 'failing' ? 'aih-defined aih-defined--failing' : 'aih-defined'}>
      <header className="aih-defined__head">
        <ProviderMark providerType={account.providerType} />
        <a
          className="aih-defined__title"
          href={basePath}
          onClick={(event) => {
            event.preventDefault();
            navigation.navigate(basePath);
          }}
        >
          <span className="aih-defined__name">{account.name}</span>
          <span className="aih-muted">
            {t('hub.type.email.name')} · {PROVIDER_LABELS[account.providerType]}
          </span>
        </a>
        <StatusPill tone={HEALTH_TONES[health]}>{t(HEALTH_LABELS[health])}</StatusPill>
      </header>
      <dl className="aih-mini">
        <div>
          <dt>{t('smtp.col.environment')}</dt>
          <dd>{t(account.environment === 'production' ? 'smtp.env.production' : 'smtp.env.test')}</dd>
        </div>
        <div>
          <dt>{t('hub.card.lastTest')}</dt>
          <dd>{formatDate(account.lastTestAt, locale.locale) ?? t('smtp.never')}</dd>
        </div>
        <div>
          <dt>{t('hub.card.lastSend')}</dt>
          <dd>{formatDate(account.lastSuccessSendAt, locale.locale) ?? t('smtp.never')}</dd>
        </div>
      </dl>
      {health === 'failing' && (
        <button type="button" className="aih-button aih-button--primary aih-button--sm" onClick={() => navigation.navigate(basePath)}>
          {t('hub.fix')}
        </button>
      )}
    </article>
  );
}

function matchesFilter(account: SmtpAccount, filter: Filter): boolean {
  if (filter === 'problems') return accountHealth(account) === 'failing';
  if (filter === 'production' || filter === 'test') return account.environment === filter;
  return true;
}

function filterLabel(filter: Filter, t: ReturnType<typeof useTranslation>): string {
  if (filter === 'problems') return t('hub.filter.problems');
  if (filter === 'production') return t('smtp.env.production');
  if (filter === 'test') return t('smtp.env.test');
  return t('hub.filter.all');
}

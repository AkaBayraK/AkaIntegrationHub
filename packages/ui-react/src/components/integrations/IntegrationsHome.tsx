import { useEffect, useMemo, useState } from 'react';
import type { SmtpAccount } from '../../api/types';
import { useAkaIntegration, useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';
import { useHubClient, useHubSession } from '../../session';
import { ErrorNotice, formatDate } from '../smtp/shared';
import { PROVIDER_LABELS } from '../smtp/providers';
import { HEALTH_KEYS, INTEGRATION_TYPES, IntegrationIcon, smtpHealth, type Health, type IntegrationType } from './catalog';

type Filter = 'all' | 'problem' | 'production' | 'test';

const FILTERS: readonly { id: Filter; labelKey: MessageKey }[] = [
  { id: 'all', labelKey: 'home.filter.all' },
  { id: 'problem', labelKey: 'home.filter.problem' },
  { id: 'production', labelKey: 'home.filter.production' },
  { id: 'test', labelKey: 'home.filter.test' },
];

function matches(filter: Filter, account: SmtpAccount): boolean {
  if (filter === 'problem') return smtpHealth(account) === 'failed';
  if (filter === 'production' || filter === 'test') return account.environment === filter;
  return true;
}

export function HealthBadge({ health }: { health: Health }) {
  const t = useTranslation();
  return <span className={`aih-health aih-health--${health}`}>{t(HEALTH_KEYS[health])}</span>;
}

function TypeTile({ type, count, canWrite }: { type: IntegrationType; count: number | null; canWrite: boolean }) {
  const t = useTranslation();
  const { navigation } = useAkaIntegration();
  const name = t(type.nameKey);
  const available = type.path !== null;

  return (
    <li className={`aih-tile aih-tile--${type.id}${available ? '' : ' aih-tile--soon'}`}>
      <div className="aih-tile__head">
        <span className="aih-type-icon">
          <IntegrationIcon type={type.id} />
        </span>
        {available ? (
          <span className="aih-tile__count">
            {count ?? '–'} {t('home.defined')}
          </span>
        ) : (
          <span className="aih-chip">{t('home.comingSoon')}</span>
        )}
      </div>
      {available ? (
        <a
          className="aih-tile__name aih-stretched"
          href={type.path!}
          onClick={(event) => {
            event.preventDefault();
            navigation.navigate(type.path!);
          }}
        >
          {name}
        </a>
      ) : (
        <span className="aih-tile__name">{name}</span>
      )}
      <p className="aih-tile__desc">{t(type.descriptionKey)}</p>
      {available && canWrite && (
        <button
          type="button"
          className="aih-button aih-button--ghost aih-button--sm aih-tile__add"
          aria-label={`${t('home.add')}: ${name}`}
          onClick={() => navigation.navigate(`${type.path}/new`)}
        >
          + {t('home.add')}
        </button>
      )}
    </li>
  );
}

function ConnectionCard({ account }: { account: SmtpAccount }) {
  const t = useTranslation();
  const { navigation, locale } = useAkaIntegration();
  const health = smtpHealth(account);
  const smtpType = INTEGRATION_TYPES[0]!;
  const detailPath = `${smtpType.path}?account=${encodeURIComponent(account.id)}`;
  const open = () => navigation.navigate(detailPath);

  return (
    <li className={`aih-conn${health === 'failed' ? ' aih-conn--problem' : ''}`}>
      <div className="aih-conn__head">
        <span className="aih-type-icon aih-tile--smtp">
          <IntegrationIcon type="smtp" />
        </span>
        <div className="aih-conn__title">
          <a
            href={detailPath}
            className="aih-conn__name"
            onClick={(event) => {
              event.preventDefault();
              open();
            }}
          >
            {account.name}
          </a>
          <span className="aih-muted">
            {t('type.smtp')} · {PROVIDER_LABELS[account.providerType]}
          </span>
        </div>
        <HealthBadge health={health} />
      </div>
      <dl className="aih-conn__metrics">
        <div>
          <dt>{t('metric.environment')}</dt>
          <dd>{t(account.environment === 'production' ? 'smtp.env.production' : 'smtp.env.test')}</dd>
        </div>
        <div>
          <dt>{t('metric.lastTest')}</dt>
          <dd>{formatDate(account.lastTestAt, locale.locale) ?? t('smtp.never')}</dd>
        </div>
        <div>
          <dt>{t('metric.lastSend')}</dt>
          <dd>{formatDate(account.lastSuccessSendAt, locale.locale) ?? t('smtp.never')}</dd>
        </div>
      </dl>
      <div className="aih-conn__foot">
        <span className="aih-muted aih-truncate">{account.senderAddress}</span>
        <button
          type="button"
          className={`aih-button aih-button--sm ${health === 'failed' ? 'aih-button--danger' : 'aih-button--ghost'}`}
          aria-label={`${t(health === 'failed' ? 'home.fix' : 'home.manage')}: ${account.name}`}
          onClick={open}
        >
          {t(health === 'failed' ? 'home.fix' : 'home.manage')}
        </button>
      </div>
    </li>
  );
}

/** Entegrasyonlar ana sayfası: üstte eklenebilecek türler, altta tanımlı bağlantılar. */
export function IntegrationsHome() {
  const t = useTranslation();
  const client = useHubClient();
  const session = useHubSession();
  const tenantId = session.me?.tenant.id ?? null;
  const canRead = session.can('smtp-account:read');
  const canWrite = session.can('smtp-account:write');

  const [accounts, setAccounts] = useState<SmtpAccount[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!tenantId || !canRead) return;
    let cancelled = false;
    setError(null);
    client
      .listSmtpAccounts(tenantId, { limit: 200 })
      .then((page) => !cancelled && setAccounts(page.items))
      .catch((err: unknown) => !cancelled && setError(err));
    return () => {
      cancelled = true;
    };
  }, [client, tenantId, canRead, nonce]);

  const visible = useMemo(() => (accounts ?? []).filter((a) => matches(filter, a)), [accounts, filter]);

  if (session.loading) return <p role="status">{t('common.loading')}</p>;
  if (session.error) return <ErrorNotice error={session.error} onRetry={session.reload} />;

  const total = accounts?.length ?? 0;
  const problems = (accounts ?? []).filter((a) => smtpHealth(a) === 'failed').length;
  const healthy = (accounts ?? []).filter((a) => smtpHealth(a) === 'healthy').length;

  return (
    <div className="aih-page aih-home">
      <div className="aih-row aih-row--between">
        <div>
          <h1>{t('home.title')}</h1>
          <p className="aih-muted">{t('home.description')}</p>
        </div>
        {accounts && total > 0 && (
          <p className="aih-summary" role="status">
            <span>
              <strong>
                {healthy}/{total}
              </strong>{' '}
              {t('home.healthy')}
            </span>
            {problems > 0 && (
              <span className="aih-summary__problem">
                <strong>{problems}</strong> {t('home.problems')}
              </span>
            )}
          </p>
        )}
      </div>

      <section className="aih-section" aria-labelledby="aih-home-add">
        <div>
          <h2 id="aih-home-add">{t('home.addTitle')}</h2>
          <p className="aih-muted">{t('home.addHint')}</p>
        </div>
        <ul className="aih-tiles">
          {INTEGRATION_TYPES.map((type) => (
            <TypeTile
              key={type.id}
              type={type}
              count={type.id === 'smtp' ? (accounts?.length ?? null) : null}
              canWrite={canWrite}
            />
          ))}
        </ul>
      </section>

      <section className="aih-section" aria-labelledby="aih-home-defined">
        <div className="aih-row aih-row--between">
          <h2 id="aih-home-defined">{t('home.definedTitle')}</h2>
          <div className="aih-chips" role="group" aria-label={t('home.filterLabel')}>
            {FILTERS.map((f) => (
              <button
                key={f.id}
                type="button"
                className={`aih-chip-button${filter === f.id ? ' aih-chip-button--active' : ''}`}
                aria-pressed={filter === f.id}
                onClick={() => setFilter(f.id)}
              >
                {t(f.labelKey)}
              </button>
            ))}
          </div>
        </div>
        {!canRead ? (
          <p className="aih-card aih-muted">{t('common.forbidden')}</p>
        ) : error !== null ? (
          <ErrorNotice error={error} onRetry={() => setNonce((n) => n + 1)} />
        ) : accounts === null ? (
          <p role="status">{t('common.loading')}</p>
        ) : visible.length === 0 ? (
          <p className="aih-card aih-muted">{total === 0 ? t('home.definedEmpty') : t('home.filterEmpty')}</p>
        ) : (
          <ul className="aih-conns">
            {visible.map((account) => (
              <ConnectionCard key={account.id} account={account} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

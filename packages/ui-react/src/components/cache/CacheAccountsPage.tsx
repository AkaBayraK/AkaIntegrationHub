import { useCallback, useEffect, useState } from 'react';
import type { CacheAccount, CacheConnectionTest, CacheServerInfo } from '../../api/types';
import { useAkaIntegration, useTranslation } from '../../context';
import { useHubClient, useHubSession } from '../../session';
import { ConsolePanel } from '../console/ConsolePanel';
import {
  accountHealth,
  Badge,
  ErrorNotice,
  formatDate,
  HEALTH_LABELS,
  HEALTH_TONES,
  StatusPill,
  TypeMark,
} from '../smtp/shared';
import { ActionButton, DetailHero, InfoTiles, SectionTitle, StepTimeline } from '../ui/Detail';
import { CacheAccountForm } from './CacheAccountForm';

export const CACHE_BASE_PATH = '/admin/cache/providers';

type Mode = { kind: 'view' } | { kind: 'create' } | { kind: 'edit'; account: CacheAccount };
type Translate = ReturnType<typeof useTranslation>;

const SECONDS_PER_HOUR = 3600;
const HOURS_PER_DAY = 24;

export function CacheAccountsPage({ homePath = '/' }: { homePath?: string }) {
  const t = useTranslation();
  const { navigation } = useAkaIntegration();
  const client = useHubClient();
  const session = useHubSession();
  const tenantId = session.me?.tenant.id ?? null;
  const canWrite = session.can('cache-account:write');
  const [accounts, setAccounts] = useState<CacheAccount[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>({ kind: 'view' });
  const [error, setError] = useState<unknown>(null);
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<CacheConnectionTest | null>(null);

  const load = useCallback(async () => {
    if (!tenantId) return;
    setError(null);
    try {
      setAccounts((await client.listCacheAccounts(tenantId, { limit: 200 })).items);
    } catch (err) {
      setError(err);
    }
  }, [client, tenantId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runTest(account: CacheAccount) {
    setTesting(true);
    setResult(null);
    try {
      setResult(await client.testCacheConnection(account.tenantId, account.id));
      await load();
    } catch (err) {
      setError(err);
    } finally {
      setTesting(false);
    }
  }

  if (session.loading) return <p role="status">{t('common.loading')}</p>;
  if (session.error) return <ErrorNotice error={session.error} onRetry={session.reload} />;

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
        <span>{t('hub.type.cache.name')}</span>
      </nav>
      <div className="aih-row aih-row--between">
        <div className="aih-row aih-page-title">
          <TypeMark type="cache" />
          <div>
            <h1>{t('cache.title')}</h1>
            <p className="aih-muted">{t('cache.description')}</p>
          </div>
        </div>
        {canWrite && mode.kind === 'view' && (
          <button type="button" className="aih-button aih-button--primary" onClick={() => setMode({ kind: 'create' })}>
            + {t('cache.new')}
          </button>
        )}
      </div>

      {error !== null && <ErrorNotice error={error} onRetry={() => void load()} />}
      {mode.kind !== 'view' && tenantId ? (
        <CacheAccountForm
          tenantId={tenantId}
          account={mode.kind === 'edit' ? mode.account : null}
          onCancel={() => setMode({ kind: 'view' })}
          onSaved={(saved) => {
            setMode({ kind: 'view' });
            setSelectedId(saved.id);
            void load();
          }}
        />
      ) : accounts === null && error === null ? (
        <p role="status">{t('common.loading')}</p>
      ) : !selected ? (
        <p className="aih-card aih-muted">{t('cache.empty')}</p>
      ) : (
        <div className="aih-split">
          <div className="aih-surface aih-list">
            <ul aria-label={t('cache.list.label')}>
              {(accounts ?? []).map((account) => {
                const health = accountHealth(account);
                return (
                  <li key={account.id}>
                    <button
                      type="button"
                      className={account.id === selected.id ? 'aih-list__item aih-list__item--active' : 'aih-list__item'}
                      aria-current={account.id === selected.id ? 'true' : undefined}
                      onClick={() => {
                        setSelectedId(account.id);
                        setResult(null);
                      }}
                    >
                      <TypeMark type="cache" />
                      <span className="aih-list__text">
                        <span className="aih-list__name">{account.name}</span>
                        <span className="aih-list__sub">{`${account.host}:${account.port}`}</span>
                      </span>
                      <span className={`aih-dot aih-dot--${HEALTH_TONES[health]}`} title={t(HEALTH_LABELS[health])} />
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
          <CacheDetail
            account={selected}
            testing={testing}
            result={result?.accountId === selected.id ? result : null}
            onTest={() => void runTest(selected)}
            onEdit={canWrite ? () => setMode({ kind: 'edit', account: selected }) : undefined}
          />
        </div>
      )}
    </div>
  );
}

function CacheDetail({
  account,
  testing,
  result,
  onTest,
  onEdit,
}: {
  account: CacheAccount;
  testing: boolean;
  result: CacheConnectionTest | null;
  onTest: () => void;
  onEdit?: () => void;
}) {
  const t = useTranslation();
  const { locale } = useAkaIntegration();
  const session = useHubSession();
  const health = accountHealth(account);
  const headingId = `aih-cache-${account.id}`;
  const provider = account.providerType === 'valkey' ? 'Valkey' : t('cache.provider.redis');
  const environment = t(account.environment === 'production' ? 'smtp.env.production' : 'smtp.env.test');
  return (
    <section className="aih-surface aih-detail" aria-labelledby={headingId}>
      <DetailHero
        mark={<TypeMark type="cache" />}
        title={account.name}
        titleId={headingId}
        subtitle={`${provider}${account.serverVersion ? ` ${account.serverVersion}` : ''} · ${environment}`}
        badges={
          <>
            <StatusPill tone={HEALTH_TONES[health]}>{t(HEALTH_LABELS[health])}</StatusPill>
            {account.isDefault && <Badge tone="accent">{t('smtp.default')}</Badge>}
          </>
        }
        actions={
          <>
            {session.can('cache-account:test') && (
              <ActionButton
                icon="play"
                variant="primary"
                label={testing ? t('common.loading') : t('smtp.action.test')}
                onClick={onTest}
                disabled={testing}
                ariaLabel={`${t('smtp.action.test')}: ${account.name}`}
              />
            )}
            {onEdit && (
              <ActionButton
                icon="pencil"
                label={t('smtp.action.edit')}
                onClick={onEdit}
                ariaLabel={`${t('smtp.action.edit')}: ${account.name}`}
              />
            )}
          </>
        }
      />
      <InfoTiles
        label={t('detail.facts')}
        items={[
          { icon: 'server', label: t('smtp.col.host'), value: `${account.host}:${account.port}`, mono: true },
          { icon: 'database', label: t('cache.form.database'), value: `db${account.databaseIndex}`, mono: true },
          {
            icon: account.tlsEnabled ? 'lock' : 'shield',
            label: t('smtp.detail.security'),
            value: `${t(account.tlsEnabled ? 'cache.tls.on' : 'cache.tls.off')} · ${t(`cache.auth.${account.authMode}` as const)}`,
          },
          { icon: 'tag', label: t('cache.form.prefix'), value: account.keyPrefix ?? '—', mono: true },
          { icon: 'timer', label: t('smtp.detail.timeout'), value: `${account.timeoutSeconds} ${t('smtp.detail.seconds')}` },
          {
            icon: 'clock',
            label: t('smtp.detail.lastTest'),
            value: formatDate(account.lastTestAt, locale.locale) ?? t('smtp.detail.notTested'),
          },
        ]}
      />
      {result && <CacheTestResult result={result} t={t} />}
      <ConsolePanel url={account.consoleUrl} title={account.name} />
    </section>
  );
}

function CacheTestResult({ result, t }: { result: CacheConnectionTest; t: Translate }) {
  return (
    <div className="aih-detail__section" role="status">
      <SectionTitle
        icon="activity"
        aside={
          <span className="aih-row">
            <Badge tone={result.outcome === 'passed' ? 'success' : 'danger'}>
              {t(result.outcome === 'passed' ? 'smtp.test.passed' : 'smtp.test.failed')}
            </Badge>
            <span className="aih-muted">{result.durationMs} ms</span>
          </span>
        }
      >
        {t('smtp.testResult.title')}
      </SectionTitle>
      <StepTimeline steps={result.steps} />
      {result.server && <ServerSummary server={result.server} t={t} />}
    </div>
  );
}

function formatUptime(seconds: number | null): string {
  if (seconds === null) return '—';
  const hours = Math.floor(seconds / SECONDS_PER_HOUR);
  return hours >= HOURS_PER_DAY ? `${Math.floor(hours / HOURS_PER_DAY)} g ${hours % HOURS_PER_DAY} sa` : `${hours} sa`;
}

function ServerSummary({ server, t }: { server: CacheServerInfo; t: Translate }) {
  const keys = Object.entries(server.keyspace);
  const total = keys.reduce((sum, [, count]) => sum + count, 0);
  return (
    <>
      <SectionTitle icon="cpu">{t('cache.server.title')}</SectionTitle>
      <InfoTiles
        size="lg"
        label={t('cache.server.title')}
        items={[
          {
            icon: 'server',
            label: t('cache.server.version'),
            value: `${server.serverName ?? ''} ${server.version ?? ''}`.trim() || '—',
            tone: 'accent',
          },
          { icon: 'cpu', label: t('cache.server.memory'), value: server.usedMemory ?? '—' },
          { icon: 'users', label: t('cache.server.clients'), value: server.connectedClients ?? '—' },
          {
            icon: 'key',
            label: t('cache.server.keys'),
            value: keys.length > 1 ? `${total} (${keys.map(([db, count]) => `${db}: ${count}`).join(' · ')})` : total,
          },
          { icon: 'clock', label: t('cache.server.uptime'), value: formatUptime(server.uptimeSeconds), tone: 'success' },
        ]}
      />
    </>
  );
}

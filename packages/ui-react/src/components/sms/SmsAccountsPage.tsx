import { useCallback, useEffect, useState, type FormEvent } from 'react';
import type { SmsAccount, SmsCreditTransaction, SmsMessage } from '../../api/types';
import { useAkaIntegration, useTranslation } from '../../context';
import { useHubClient, useHubSession } from '../../session';
import { ConsolePanel } from '../console/ConsolePanel';
import {
  accountHealth,
  Badge,
  ErrorNotice,
  Field,
  formatDate,
  HEALTH_LABELS,
  HEALTH_TONES,
  healthClass,
  StatusPill,
  TypeMark,
  type HealthTone,
} from '../smtp/shared';
import { ActionButton, DetailHero, InfoTiles, SectionTitle } from '../ui/Detail';
import { SmsAccountForm } from './SmsAccountForm';

export const SMS_BASE_PATH = '/admin/sms/providers';

type Mode = { kind: 'view' } | { kind: 'create' } | { kind: 'edit'; account: SmsAccount };
type Panel = 'none' | 'credit' | 'test';
type Translate = ReturnType<typeof useTranslation>;

const PROVIDER_LABELS: Record<SmsAccount['providerType'], string> = {
  mock_test: 'Test',
  netgsm: 'Netgsm',
  iletimerkezi: 'İleti Merkezi',
  verimor: 'Verimor',
  turkcell: 'Turkcell',
};

const STATUS_TONES = { queued: 'neutral', sent: 'success', failed: 'danger', unknown: 'warning' } as const;

function newKey(): string {
  return `ui-${globalThis.crypto.randomUUID()}`;
}

function smsTone(account: SmsAccount): HealthTone {
  const tone = HEALTH_TONES[accountHealth(account)];
  return account.lowCredit && tone === 'success' ? 'warning' : tone;
}

export function SmsAccountsPage({ homePath = '/' }: { homePath?: string }) {
  const t = useTranslation();
  const { navigation } = useAkaIntegration();
  const client = useHubClient();
  const session = useHubSession();
  const tenantId = session.me?.tenant.id ?? null;
  const canWrite = session.can('sms-account:write');
  const [accounts, setAccounts] = useState<SmsAccount[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>({ kind: 'view' });
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(async () => {
    if (!tenantId) return;
    setError(null);
    try {
      setAccounts((await client.listSmsAccounts(tenantId, { limit: 200 })).items);
    } catch (err) {
      setError(err);
    }
  }, [client, tenantId]);

  useEffect(() => {
    void load();
  }, [load]);

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
        <span>{t('hub.type.sms.name')}</span>
      </nav>
      <div className="aih-row aih-row--between">
        <div className="aih-row aih-page-title">
          <TypeMark type="sms" />
          <div>
            <h1>{t('sms.title')}</h1>
            <p className="aih-muted">{t('sms.description')}</p>
          </div>
        </div>
        {canWrite && mode.kind === 'view' && (
          <button type="button" className="aih-button aih-button--primary" onClick={() => setMode({ kind: 'create' })}>
            + {t('sms.new')}
          </button>
        )}
      </div>

      {error !== null && <ErrorNotice error={error} onRetry={() => void load()} />}
      {mode.kind !== 'view' && tenantId ? (
        <SmsAccountForm
          tenantId={tenantId}
          account={mode.kind === 'edit' ? mode.account : null}
          onCancel={() => setMode({ kind: 'view' })}
          onSaved={(saved) => {
            setMode({ kind: 'view' });
            setSelectedId(saved.id);
            void load();
          }}
        />
      ) : accounts === null ? (
        error === null && <p role="status">{t('common.loading')}</p>
      ) : !selected ? (
        <p className="aih-card aih-muted">{t('sms.empty')}</p>
      ) : (
        <div className="aih-split">
          <div className="aih-surface aih-list">
            <ul aria-label={t('sms.list.label')}>
              {(accounts ?? []).map((account) => {
                const tone = smsTone(account);
                return (
                  <li key={account.id}>
                    <button
                      type="button"
                      className={healthClass(tone, 'aih-list__item', account.id === selected.id ? 'aih-list__item--active' : '')}
                      aria-current={account.id === selected.id ? 'true' : undefined}
                      onClick={() => setSelectedId(account.id)}
                    >
                      <TypeMark type="sms" />
                      <span className="aih-list__text">
                        <span className="aih-list__name">{account.name}</span>
                        <span className="aih-list__sub">
                          {PROVIDER_LABELS[account.providerType]} · {account.creditBalance} {t('sms.credit.unit')}
                        </span>
                      </span>
                      <span className={`aih-dot aih-dot--${tone}`} title={t(HEALTH_LABELS[accountHealth(account)])} />
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
          <SmsDetail
            key={selected.id}
            account={selected}
            onChanged={() => void load()}
            onEdit={canWrite ? () => setMode({ kind: 'edit', account: selected }) : undefined}
          />
        </div>
      )}
    </div>
  );
}

function SmsDetail({ account, onChanged, onEdit }: { account: SmsAccount; onChanged: () => void; onEdit?: () => void }) {
  const t = useTranslation();
  const { locale } = useAkaIntegration();
  const client = useHubClient();
  const session = useHubSession();
  const [panel, setPanel] = useState<Panel>('none');
  const [messages, setMessages] = useState<SmsMessage[]>([]);
  const [credits, setCredits] = useState<SmsCreditTransaction[]>([]);
  const [error, setError] = useState<unknown>(null);
  const tone = smsTone(account);
  const headingId = `aih-sms-${account.id}`;

  const loadActivity = useCallback(async () => {
    try {
      const [page, history] = await Promise.all([
        client.listSmsMessages(account.tenantId, { accountId: account.id, limit: 10 }),
        client.smsCreditHistory(account.tenantId, account.id),
      ]);
      setMessages(page.items);
      setCredits(history.slice(0, 10));
    } catch (err) {
      setError(err);
    }
  }, [client, account.tenantId, account.id]);

  useEffect(() => {
    void loadActivity();
  }, [loadActivity, account.version, account.creditBalance]);

  const done = () => {
    setPanel('none');
    onChanged();
  };

  return (
    <section className={healthClass(tone, 'aih-surface', 'aih-detail')} aria-labelledby={headingId}>
      <DetailHero
        mark={<TypeMark type="sms" />}
        title={account.name}
        titleId={headingId}
        subtitle={`${PROVIDER_LABELS[account.providerType]} · ${t(
          account.environment === 'production' ? 'smtp.env.production' : 'smtp.env.test',
        )}`}
        badges={
          <>
            <StatusPill tone={HEALTH_TONES[accountHealth(account)]}>{t(HEALTH_LABELS[accountHealth(account)])}</StatusPill>
            {account.isDefault && <Badge tone="accent">{t('smtp.default')}</Badge>}
            {account.lowCredit && <StatusPill tone="warning">{t('sms.credit.low')}</StatusPill>}
          </>
        }
        actions={
          <>
            {session.can('sms-account:test') && account.enabled && (
              <ActionButton
                icon="send"
                variant="primary"
                label={t('sms.action.test')}
                onClick={() => setPanel(panel === 'test' ? 'none' : 'test')}
                ariaLabel={`${t('sms.action.test')}: ${account.name}`}
              />
            )}
            {session.can('sms-credit:manage') && (
              <ActionButton
                icon="gauge"
                label={t('sms.action.credit')}
                onClick={() => setPanel(panel === 'credit' ? 'none' : 'credit')}
                ariaLabel={`${t('sms.action.credit')}: ${account.name}`}
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
      {panel === 'credit' && <CreditPanel account={account} onDone={done} onCancel={() => setPanel('none')} />}
      {panel === 'test' && <TestSmsPanel account={account} onDone={done} onCancel={() => setPanel('none')} />}
      <InfoTiles
        label={t('detail.facts')}
        items={[
          {
            icon: 'gauge',
            label: t('sms.credit.balance'),
            value: `${account.creditBalance.toLocaleString(locale.locale)} ${t('sms.credit.unit')}`,
            tone: account.lowCredit ? 'warning' : 'success',
          },
          { icon: 'tag', label: t('sms.form.header'), value: account.senderHeader, mono: true },
          { icon: 'server', label: t('sms.form.provider'), value: PROVIDER_LABELS[account.providerType] },
          {
            icon: 'key',
            label: t('smtp.detail.security'),
            value: account.hasSecret ? t('license.keyStored') : t('sms.credentials.none'),
          },
          { icon: 'info', label: t('sms.form.threshold'), value: `${account.lowCreditThreshold} ${t('sms.credit.unit')}` },
          {
            icon: 'clock',
            label: t('smtp.detail.lastTest'),
            value: formatDate(account.lastTestAt, locale.locale) ?? t('smtp.detail.notTested'),
          },
        ]}
      />
      {error !== null && <ErrorNotice error={error} />}
      <div className="aih-detail__section">
        <SectionTitle icon="send">{t('sms.messages.title')}</SectionTitle>
        <MessageTable messages={messages} t={t} locale={locale.locale} />
      </div>
      <div className="aih-detail__section">
        <SectionTitle icon="gauge">{t('sms.credit.history')}</SectionTitle>
        <CreditList credits={credits} t={t} locale={locale.locale} />
      </div>
      <ConsolePanel url={account.consoleUrl} title={account.name} />
    </section>
  );
}

function CreditPanel({ account, onDone, onCancel }: { account: SmsAccount; onDone: () => void; onCancel: () => void }) {
  const t = useTranslation();
  const client = useHubClient();
  const [quantity, setQuantity] = useState(1000);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await client.loadSmsCredit(account.tenantId, account.id, quantity, reason.trim() || undefined);
      onDone();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="aih-panel aih-inline-form" onSubmit={(event) => void submit(event)}>
      <SectionTitle icon="gauge">{t('sms.action.credit')}</SectionTitle>
      <div className="aih-grid-3">
        <Field id="aih-sms-credit" label={t('sms.credit.quantity')}>
          <input
            id="aih-sms-credit"
            className="aih-input"
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
          />
        </Field>
        <Field id="aih-sms-credit-reason" label={t('sms.credit.reason')}>
          <input
            id="aih-sms-credit-reason"
            className="aih-input"
            maxLength={200}
            placeholder={t('sms.credit.reasonHint')}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </Field>
      </div>
      {error !== null && <ErrorNotice error={error} />}
      <div className="aih-row">
        <button type="submit" className="aih-button aih-button--primary" disabled={busy || quantity < 1}>
          {busy ? t('common.loading') : t('sms.credit.submit')}
        </button>
        <button type="button" className="aih-button aih-button--ghost" onClick={onCancel} disabled={busy}>
          {t('common.cancel')}
        </button>
      </div>
    </form>
  );
}

function TestSmsPanel({ account, onDone, onCancel }: { account: SmsAccount; onDone: () => void; onCancel: () => void }) {
  const t = useTranslation();
  const client = useHubClient();
  const [phone, setPhone] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<SmsMessage | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [key] = useState(newKey);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setResult(await client.sendTestSms(account.tenantId, account.id, phone, key));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="aih-panel aih-inline-form" onSubmit={(event) => void submit(event)}>
      <SectionTitle icon="send">{t('sms.action.test')}</SectionTitle>
      <p className="aih-notice">{t(account.providerType === 'mock_test' ? 'sms.test.mockNote' : 'sms.test.realNote')}</p>
      <Field id="aih-sms-test-phone" label={t('sms.test.phone')}>
        <input
          id="aih-sms-test-phone"
          className="aih-input"
          type="tel"
          inputMode="tel"
          placeholder="0532 123 45 67"
          value={phone}
          disabled={result !== null}
          onChange={(e) => setPhone(e.target.value)}
        />
      </Field>
      {result && (
        <p role="status">
          <StatusPill tone={STATUS_TONES[result.status]}>{t(`sms.status.${result.status}` as const)}</StatusPill>{' '}
          <span className="aih-muted">
            {result.phoneMasked} · {result.creditCost} {t('sms.credit.unit')}
            {result.errorCode ? ` · ${result.errorCode}` : ''}
          </span>
        </p>
      )}
      {error !== null && <ErrorNotice error={error} />}
      <div className="aih-row">
        {result ? (
          <button type="button" className="aih-button aih-button--primary" onClick={onDone}>
            {t('common.close')}
          </button>
        ) : (
          <>
            <button type="submit" className="aih-button aih-button--primary" disabled={busy || phone.trim().length < 10}>
              {busy ? t('common.loading') : t('sms.test.submit')}
            </button>
            <button type="button" className="aih-button aih-button--ghost" onClick={onCancel} disabled={busy}>
              {t('common.cancel')}
            </button>
          </>
        )}
      </div>
    </form>
  );
}

function MessageTable({ messages, t, locale }: { messages: SmsMessage[]; t: Translate; locale: string }) {
  if (messages.length === 0) return <p className="aih-muted">{t('sms.messages.empty')}</p>;
  return (
    <div className="aih-table-wrap">
      <table className="aih-table">
        <thead>
          <tr>
            <th scope="col">{t('sms.messages.status')}</th>
            <th scope="col">{t('sms.messages.phone')}</th>
            <th scope="col">{t('sms.messages.purpose')}</th>
            <th scope="col">{t('sms.messages.cost')}</th>
            <th scope="col">{t('sms.messages.date')}</th>
          </tr>
        </thead>
        <tbody>
          {messages.map((m) => (
            <tr key={m.id}>
              <td>
                <StatusPill tone={STATUS_TONES[m.status]}>{t(`sms.status.${m.status}` as const)}</StatusPill>
                {m.errorCode && <code className="aih-table__code">{m.errorCode}</code>}
              </td>
              <td>
                <code>{m.phoneMasked}</code>
              </td>
              <td>
                {t(`sms.purpose.${m.purpose}` as const)}
                {m.kind === 'test' && <Badge tone="neutral">{t('sms.messages.test')}</Badge>}
              </td>
              <td>
                {m.creditCost} {t('sms.credit.unit')}
              </td>
              <td>{formatDate(m.createdAt, locale)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CreditList({ credits, t, locale }: { credits: SmsCreditTransaction[]; t: Translate; locale: string }) {
  if (credits.length === 0) return <p className="aih-muted">{t('sms.credit.empty')}</p>;
  return (
    <ul className="aih-ledger">
      {credits.map((c) => (
        <li key={c.id} className={c.quantity > 0 ? 'aih-ledger__row aih-ledger__row--in' : 'aih-ledger__row aih-ledger__row--out'}>
          <span className="aih-ledger__kind">{t(`sms.credit.kind.${c.kind}` as const)}</span>
          <span className="aih-muted">{c.reason ?? ''}</span>
          <strong className="aih-ledger__qty">
            {c.quantity > 0 ? '+' : ''}
            {c.quantity}
          </strong>
          <span className="aih-muted">
            = {c.balanceAfter} · {formatDate(c.createdAt, locale)}
          </span>
        </li>
      ))}
    </ul>
  );
}

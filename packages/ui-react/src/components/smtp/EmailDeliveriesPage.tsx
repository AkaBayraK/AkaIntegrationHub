import { useCallback, useEffect, useState } from 'react';
import type { DeliveryStatus, EmailDelivery } from '../../api/types';
import { useAkaIntegration, useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';
import { useHubClient, useHubSession } from '../../session';
import { Badge, ErrorNotice, formatDate } from './shared';

const STATUSES: DeliveryStatus[] = ['queued', 'sending', 'accepted_by_smtp', 'failed', 'retry_scheduled', 'cancelled'];

export function EmailDeliveriesPage() {
  const t = useTranslation();
  const { locale } = useAkaIntegration();
  const client = useHubClient();
  const session = useHubSession();
  const tenantId = session.me?.tenant.id ?? null;
  const [status, setStatus] = useState<DeliveryStatus | ''>('');
  const [rows, setRows] = useState<EmailDelivery[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(async () => {
    if (!tenantId) return;
    setError(null);
    try {
      setRows(await client.listEmailDeliveries(tenantId, { status: status || undefined, limit: 100 }));
    } catch (err) {
      setError(err);
    }
  }, [client, tenantId, status]);

  useEffect(() => {
    void load();
  }, [load]);

  if (session.loading) return <p role="status">{t('common.loading')}</p>;
  if (session.error) return <ErrorNotice error={session.error} onRetry={session.reload} />;

  return (
    <div className="aih-page">
      <h1>{t('deliveries.title')}</h1>
      <p className="aih-notice">{t('deliveries.note')}</p>
      <div className="aih-filters">
        <label className="aih-field">
          <span>{t('deliveries.col.status')}</span>
          <select className="aih-select" value={status} onChange={(e) => setStatus(e.target.value as DeliveryStatus | '')}>
            <option value="">{t('common.all')}</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {t(`deliveries.status.${s}` as MessageKey)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error !== null && <ErrorNotice error={error} onRetry={() => void load()} />}
      {rows === null && error === null ? (
        <p role="status">{t('common.loading')}</p>
      ) : rows && rows.length === 0 ? (
        <p className="aih-card aih-muted">{t('deliveries.empty')}</p>
      ) : rows ? (
        <div className="aih-table-wrap">
          <table className="aih-table">
            <caption className="aih-visually-hidden">{t('deliveries.title')}</caption>
            <thead>
              <tr>
                <th scope="col">{t('deliveries.col.time')}</th>
                <th scope="col">{t('deliveries.col.recipient')}</th>
                <th scope="col">{t('deliveries.col.subject')}</th>
                <th scope="col">{t('deliveries.col.status')}</th>
                <th scope="col">{t('deliveries.col.attempts')}</th>
                <th scope="col">{t('deliveries.col.error')}</th>
                <th scope="col">{t('common.correlationId')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{formatDate(row.createdAt, locale.locale)}</td>
                  <td>{row.recipient}</td>
                  <td>{row.subject}</td>
                  <td>
                    <Badge tone={row.status === 'accepted_by_smtp' ? 'success' : row.status === 'failed' ? 'danger' : 'neutral'}>
                      {t(`deliveries.status.${row.status}` as MessageKey)}
                    </Badge>
                  </td>
                  <td>{row.attemptCount}</td>
                  <td>{row.lastErrorCode ? <code>{row.lastErrorCode}</code> : '—'}</td>
                  <td>
                    <code>{row.correlationId ?? '—'}</code>
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

import { useRef, useState, type FormEvent } from 'react';
import { HubApiError } from '../../api/client';
import type { EmailDelivery, SmtpAccount } from '../../api/types';
import { useTranslation } from '../../context';
import { useHubClient } from '../../session';
import { Badge, ErrorNotice } from './shared';

export function SendTestEmailPanel({
  account,
  defaultRecipient,
  onClose,
}: {
  account: SmtpAccount;
  defaultRecipient?: string | null;
  onClose: () => void;
}) {
  const t = useTranslation();
  const client = useHubClient();
  const [recipient, setRecipient] = useState(defaultRecipient ?? '');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<EmailDelivery | null>(null);
  // Aynı panelde tekrar gönderimde aynı anahtar → sunucu ikinci e-postayı göndermez.
  const keyRef = useRef(`ui-${globalThis.crypto.randomUUID()}`);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!confirmed || !recipient) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await client.sendTestEmail(account.tenantId, account.id, recipient.trim(), keyRef.current));
    } catch (err) {
      setError(err);
      if (err instanceof HubApiError && err.status === 422) keyRef.current = `ui-${globalThis.crypto.randomUUID()}`;
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="aih-panel" role="dialog" aria-labelledby={`aih-send-${account.id}`}>
      <h3 id={`aih-send-${account.id}`}>
        {t('smtp.sendTest.title')} — {account.name}
      </h3>
      {result ? (
        <div aria-live="polite">
          {result.status === 'accepted_by_smtp' ? (
            <p>
              <Badge tone="success">{t('deliveries.status.accepted_by_smtp')}</Badge> {t('smtp.sendTest.accepted')}
            </p>
          ) : (
            <p>
              <Badge tone="danger">{t('smtp.sendTest.failed')}</Badge> <code>{result.lastErrorCode}</code>
            </p>
          )}
          <button type="button" className="aih-button aih-button--ghost" onClick={onClose}>
            {t('common.close')}
          </button>
        </div>
      ) : (
        <form className="aih-form" onSubmit={submit} noValidate>
          <div className="aih-field">
            <label htmlFor={`aih-send-recipient-${account.id}`}>{t('smtp.sendTest.recipient')}</label>
            <input
              id={`aih-send-recipient-${account.id}`}
              className="aih-input"
              type="email"
              autoComplete="email"
              required
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              aria-describedby={`aih-send-help-${account.id}`}
            />
            <small id={`aih-send-help-${account.id}`} className="aih-notice">
              {t('smtp.sendTest.recipientHelp')}
            </small>
          </div>
          <label className="aih-check">
            <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
            <span>{t('smtp.sendTest.confirm')}</span>
          </label>
          {error !== null && <ErrorNotice error={error} />}
          <div className="aih-row">
            <button type="submit" className="aih-button aih-button--primary" disabled={!confirmed || !recipient || busy}>
              {busy ? t('common.loading') : t('smtp.sendTest.submit')}
            </button>
            <button type="button" className="aih-button aih-button--ghost" onClick={onClose} disabled={busy}>
              {t('common.cancel')}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}

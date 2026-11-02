import type { ReactNode } from 'react';
import { HubApiError } from '../../api/client';
import { useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';

export function formatDate(value: string | null, locale: string): string | null {
  if (!value) return null;
  return new Intl.DateTimeFormat(locale === 'tr' ? 'tr-TR' : 'en-GB', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value));
}

export function Badge({ tone, children }: { tone: 'success' | 'danger' | 'neutral' | 'accent'; children: ReactNode }) {
  return <span className={`aih-badge aih-badge--${tone}`}>{children}</span>;
}

export function ErrorNotice({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const t = useTranslation();
  const forbidden = error instanceof HubApiError && error.status === 403;
  const correlationId = error instanceof HubApiError ? error.problem.correlationId : null;
  const detail = error instanceof HubApiError ? error.problem.detail : null;
  return (
    <div className="aih-alert aih-alert--danger" role="alert">
      <p>{forbidden ? t('common.forbidden') : (detail ?? t('common.error'))}</p>
      {correlationId && (
        <p className="aih-notice">
          {t('common.correlationId')}: <code>{correlationId}</code>
        </p>
      )}
      {onRetry && !forbidden && (
        <button type="button" className="aih-button aih-button--ghost" onClick={onRetry}>
          {t('common.retry')}
        </button>
      )}
    </div>
  );
}

export function ConfirmPanel({
  message,
  onConfirm,
  onCancel,
  busy,
}: {
  message: MessageKey;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
}) {
  const t = useTranslation();
  return (
    <div className="aih-panel" role="alertdialog" aria-label={t(message)}>
      <p>{t(message)}</p>
      <div className="aih-row">
        <button type="button" className="aih-button aih-button--primary" onClick={onConfirm} disabled={busy}>
          {t('common.yes')}
        </button>
        <button type="button" className="aih-button aih-button--ghost" onClick={onCancel} disabled={busy}>
          {t('common.no')}
        </button>
      </div>
    </div>
  );
}

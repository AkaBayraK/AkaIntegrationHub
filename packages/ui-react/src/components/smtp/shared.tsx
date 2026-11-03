import type { ReactNode } from 'react';
import { HubApiError } from '../../api/client';
import type { ProviderType, SmtpAccount } from '../../api/types';
import { useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';
import { Icon } from '../Icon';
import type { IntegrationTypeId } from '../integrations/catalog';

export const SMTP_BASE_PATH = '/admin/email/providers';

export const PROVIDER_LABELS: Record<ProviderType, string> = {
  custom_smtp: 'Custom SMTP',
  microsoft_365: 'Microsoft 365',
  google_workspace: 'Google Workspace',
  amazon_ses: 'Amazon SES',
  mailpit_test: 'Mailpit',
};

const PROVIDER_INITIALS: Record<ProviderType, string> = {
  custom_smtp: '⚙',
  microsoft_365: 'M',
  google_workspace: 'G',
  amazon_ses: 'A',
  mailpit_test: 'MP',
};

export type AccountHealth = 'healthy' | 'failing' | 'untested' | 'disabled';

export const HEALTH_LABELS: Record<AccountHealth, MessageKey> = {
  healthy: 'hub.health.healthy',
  failing: 'hub.health.failing',
  untested: 'hub.health.untested',
  disabled: 'hub.health.disabled',
};

export const HEALTH_TONES: Record<AccountHealth, 'success' | 'danger' | 'warning' | 'neutral'> = {
  healthy: 'success',
  failing: 'danger',
  untested: 'warning',
  disabled: 'neutral',
};

export function accountHealth(account: SmtpAccount): AccountHealth {
  if (!account.enabled) return 'disabled';
  if (account.lastTestOutcome === 'failed') return 'failing';
  if (account.lastTestOutcome === 'passed') return 'healthy';
  return 'untested';
}

export function ProviderMark({ providerType, size = 'md' }: { providerType: ProviderType; size?: 'sm' | 'md' }) {
  return (
    <span className={`aih-mark aih-mark--${size} aih-mark--${providerType}`} aria-hidden="true">
      {PROVIDER_INITIALS[providerType]}
    </span>
  );
}

export function TypeMark({ type }: { type: IntegrationTypeId }) {
  return (
    <span className={`aih-mark aih-mark--md aih-mark--type aih-mark--type-${type}`} aria-hidden="true">
      <Icon name={`type-${type}`} size={24} />
    </span>
  );
}

export function StatusPill({ tone, children }: { tone: 'success' | 'danger' | 'warning' | 'neutral' | 'accent'; children: ReactNode }) {
  return (
    <span className={`aih-pill aih-pill--${tone}`}>
      <span className="aih-pill__dot" aria-hidden="true" />
      {children}
    </span>
  );
}

export function Kpi({ label, value, hint, tone }: { label: string; value: ReactNode; hint?: ReactNode; tone?: 'danger' | 'success' }) {
  return (
    <div className="aih-kpi">
      <span className="aih-kpi__label">{label}</span>
      <strong className={tone ? `aih-kpi__value aih-kpi__value--${tone}` : 'aih-kpi__value'}>{value}</strong>
      {hint && <span className={tone ? `aih-kpi__hint aih-kpi__hint--${tone}` : 'aih-kpi__hint'}>{hint}</span>}
    </div>
  );
}

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

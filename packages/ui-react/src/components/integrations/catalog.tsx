import type { SmtpAccount } from '../../api/types';
import type { MessageKey } from '../../i18n/messages';

export type IntegrationTypeId = 'smtp' | 'sms' | 'redis' | 'rabbitmq' | 'webhook' | 'push' | 'whatsapp' | 'storage';

export interface IntegrationType {
  id: IntegrationTypeId;
  nameKey: MessageKey;
  descriptionKey: MessageKey;
  /** Türün yönetim sayfası; yoksa tür henüz backend'de bulunmaz ve "Yakında" gösterilir. */
  path: string | null;
}

export const INTEGRATION_TYPES: readonly IntegrationType[] = [
  { id: 'smtp', nameKey: 'type.smtp', descriptionKey: 'type.smtp.desc', path: '/admin/email/providers' },
  { id: 'sms', nameKey: 'type.sms', descriptionKey: 'type.sms.desc', path: null },
  { id: 'redis', nameKey: 'type.redis', descriptionKey: 'type.redis.desc', path: null },
  { id: 'rabbitmq', nameKey: 'type.rabbitmq', descriptionKey: 'type.rabbitmq.desc', path: null },
  { id: 'webhook', nameKey: 'type.webhook', descriptionKey: 'type.webhook.desc', path: null },
  { id: 'push', nameKey: 'type.push', descriptionKey: 'type.push.desc', path: null },
  { id: 'whatsapp', nameKey: 'type.whatsapp', descriptionKey: 'type.whatsapp.desc', path: null },
  { id: 'storage', nameKey: 'type.storage', descriptionKey: 'type.storage.desc', path: null },
];

export type Health = 'healthy' | 'failed' | 'untested' | 'disabled';

export const HEALTH_KEYS: Record<Health, MessageKey> = {
  healthy: 'health.healthy',
  failed: 'health.failed',
  untested: 'health.untested',
  disabled: 'health.disabled',
};

export function smtpHealth(account: Pick<SmtpAccount, 'enabled' | 'lastTestOutcome'>): Health {
  if (!account.enabled) return 'disabled';
  if (account.lastTestOutcome === 'failed') return 'failed';
  if (account.lastTestOutcome === 'passed') return 'healthy';
  return 'untested';
}

const PATHS: Record<IntegrationTypeId, string> = {
  smtp: 'M3 6h18v12H3z M3 7l9 6 9-6',
  sms: 'M4 5h16v11H9l-5 4z M8 10h.01 M12 10h.01 M16 10h.01',
  redis: 'M4 7c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z M4 7v5c0 1.7 3.6 3 8 3s8-1.3 8-3V7 M4 12v5c0 1.7 3.6 3 8 3s8-1.3 8-3v-5',
  rabbitmq: 'M3 6h12 M3 12h12 M3 18h12 M18 6l3 3-3 3 M18 12l3 3-3 3',
  webhook: 'M13 3L5 14h6l-1 7 8-11h-6z',
  push: 'M7 3h10v18H7z M11 18h2 M12 6v4 M12 13h.01',
  whatsapp: 'M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3z M9 9c0 3 3 6 6 6',
  storage: 'M3 7l3-3h12l3 3v12H3z M3 7h18 M9 12h6',
};

export function IntegrationIcon({ type, size = 22 }: { type: IntegrationTypeId; size?: number }) {
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={PATHS[type]} />
    </svg>
  );
}

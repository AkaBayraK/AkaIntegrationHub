import type { MessageKey } from '../../i18n/messages';
import { SMTP_BASE_PATH } from '../smtp/shared';

export type IntegrationTypeId = 'email' | 'cache' | 'queue' | 'sms' | 'webhook' | 'push' | 'whatsapp' | 'storage';

export interface IntegrationType {
  id: IntegrationTypeId;
  nameKey: MessageKey;
  descriptionKey: MessageKey;
  symbol: string;
  /** Yalnız backend'i hazır olan türlerin yönetim sayfası vardır; diğerleri "Yakında" görünür. */
  basePath: string | null;
}

export const INTEGRATION_TYPES: readonly IntegrationType[] = [
  { id: 'email', nameKey: 'hub.type.email.name', descriptionKey: 'hub.type.email.description', symbol: '✉', basePath: SMTP_BASE_PATH },
  { id: 'cache', nameKey: 'hub.type.cache.name', descriptionKey: 'hub.type.cache.description', symbol: '◆', basePath: null },
  { id: 'queue', nameKey: 'hub.type.queue.name', descriptionKey: 'hub.type.queue.description', symbol: '⇄', basePath: null },
  { id: 'sms', nameKey: 'hub.type.sms.name', descriptionKey: 'hub.type.sms.description', symbol: '✆', basePath: null },
  { id: 'webhook', nameKey: 'hub.type.webhook.name', descriptionKey: 'hub.type.webhook.description', symbol: '↯', basePath: null },
  { id: 'push', nameKey: 'hub.type.push.name', descriptionKey: 'hub.type.push.description', symbol: '◉', basePath: null },
  { id: 'whatsapp', nameKey: 'hub.type.whatsapp.name', descriptionKey: 'hub.type.whatsapp.description', symbol: 'W', basePath: null },
  { id: 'storage', nameKey: 'hub.type.storage.name', descriptionKey: 'hub.type.storage.description', symbol: '⛁', basePath: null },
];

import type { ProviderType } from '../../api/types';

export const PROVIDER_LABELS: Record<ProviderType, string> = {
  custom_smtp: 'Custom SMTP',
  microsoft_365: 'Microsoft 365',
  google_workspace: 'Google Workspace',
  amazon_ses: 'Amazon SES',
  mailpit_test: 'Mailpit',
};

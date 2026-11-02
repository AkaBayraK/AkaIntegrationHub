export type ProviderType = 'custom_smtp' | 'microsoft_365' | 'google_workspace' | 'amazon_ses' | 'mailpit_test';
export type TlsMode = 'starttls' | 'implicit' | 'none';
export type AuthMode = 'smtp_auth' | 'oauth2' | 'none';
export type AccountEnvironment = 'test' | 'production';
export type DeliveryStatus = 'queued' | 'sending' | 'accepted_by_smtp' | 'failed' | 'retry_scheduled' | 'cancelled';

export interface Me {
  subject: string;
  displayName: string | null;
  email: string | null;
  tenant: { id: string; slug: string; name: string };
  roles: string[];
  permissions: string[];
}

export interface SmtpCapability {
  type: ProviderType;
  label: string;
  defaultHost: string | null;
  defaultPort: number;
  defaultTls: TlsMode;
  tlsModes: TlsMode[];
  authModes: AuthMode[];
  plannedAuthModes: AuthMode[];
  environments: AccountEnvironment[];
  notes: string;
}

export interface SmtpAccountInput {
  name: string;
  providerType: ProviderType;
  host: string;
  port: number;
  tlsMode: TlsMode;
  authMode: AuthMode;
  username: string | null;
  senderAddress: string;
  senderName: string | null;
  replyTo: string | null;
  environment: AccountEnvironment;
  enabled: boolean;
  priority: number;
  timeoutSeconds: number;
  rateLimitPerMinute: number | null;
}

export interface SmtpAccountCreate extends SmtpAccountInput {
  password?: string | null;
  makeDefault?: boolean;
}

export interface SmtpAccount extends SmtpAccountInput {
  id: string;
  tenantId: string;
  projectId: string | null;
  hasSecret: boolean;
  isDefault: boolean;
  lastTestAt: string | null;
  lastTestOutcome: 'passed' | 'failed' | null;
  lastSuccessSendAt: string | null;
  version: number;
  createdAt: string;
  createdBy: string;
  updatedAt: string;
  updatedBy: string;
}

export interface Page<T> {
  items: T[];
  nextCursor: string | null;
}

export interface TestStep {
  step: string;
  outcome: 'passed' | 'failed' | 'skipped';
  durationMs: number;
  errorCode: string | null;
}

export interface ConnectionTest {
  id: string;
  accountId: string;
  testType: string;
  outcome: 'passed' | 'failed';
  errorCode: string | null;
  steps: TestStep[];
  durationMs: number;
  createdAt: string;
}

export interface DeliveryAttempt {
  attemptNo: number;
  outcome: string;
  smtpResponseClass: string | null;
  errorCode: string | null;
  durationMs: number;
  createdAt: string;
}

export interface EmailDelivery {
  id: string;
  accountId: string;
  kind: string;
  messageId: string;
  correlationId: string | null;
  idempotencyKey: string;
  recipient: string;
  subject: string;
  status: DeliveryStatus;
  attemptCount: number;
  lastErrorCode: string | null;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  attempts?: DeliveryAttempt[] | null;
}

export interface ProblemDetails {
  type?: string;
  title?: string;
  status: number;
  detail?: string;
  code?: string;
  correlationId?: string | null;
  errors?: { field: string; message: string }[];
}

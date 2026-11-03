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
  consoleUrl: string | null;
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

export type CacheProviderType = 'valkey' | 'redis';
export type CacheAuthMode = 'none' | 'password' | 'acl';
export type CacheLicenseType = 'rsal-2.0' | 'sspl-1.0' | 'agpl-3.0' | 'redis-enterprise' | 'redis-cloud';
export type CacheLicenseStatus = 'not_required' | 'valid' | 'expiring' | 'expired';

export interface CacheLicenseInput {
  type: CacheLicenseType;
  holder: string | null;
  reference: string | null;
  expiresOn: string | null;
  key?: string | null;
  acknowledged: boolean;
}

export interface CacheLicense {
  type: CacheLicenseType;
  holder: string | null;
  reference: string | null;
  expiresOn: string | null;
  hasKey: boolean;
  acknowledgedAt: string | null;
  acknowledgedBy: string | null;
}

export interface CacheCapability {
  type: CacheProviderType;
  label: string;
  defaultPort: number;
  licenseNote: string;
}

export interface CacheAccountInput {
  name: string;
  host: string;
  port: number;
  tlsEnabled: boolean;
  authMode: CacheAuthMode;
  username: string | null;
  databaseIndex: number;
  keyPrefix: string | null;
  environment: AccountEnvironment;
  enabled: boolean;
  timeoutSeconds: number;
  consoleUrl: string | null;
  license?: CacheLicenseInput | null;
}

export interface CacheAccountCreate extends CacheAccountInput {
  providerType: CacheProviderType;
  password?: string | null;
  makeDefault?: boolean;
}

export interface CacheAccount extends Omit<CacheAccountInput, 'license'> {
  id: string;
  tenantId: string;
  projectId: string | null;
  providerType: CacheProviderType;
  hasSecret: boolean;
  isDefault: boolean;
  lastTestAt: string | null;
  lastTestOutcome: 'passed' | 'failed' | null;
  serverVersion: string | null;
  license: CacheLicense | null;
  licenseStatus: CacheLicenseStatus;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface CacheServerInfo {
  serverName: string | null;
  version: string | null;
  mode: string | null;
  role: string | null;
  uptimeSeconds: number | null;
  connectedClients: number | null;
  usedMemory: string | null;
  maxMemory: string | null;
  evictionPolicy: string | null;
  keyspace: Record<string, number>;
}

export interface CacheConnectionTest {
  accountId: string;
  outcome: 'passed' | 'failed';
  errorCode: string | null;
  steps: TestStep[];
  durationMs: number;
  server: CacheServerInfo | null;
}

export type SmsProviderType = 'mock_test' | 'netgsm' | 'iletimerkezi' | 'verimor' | 'turkcell';
export type SmsPurpose = 'otp' | 'security' | 'transactional' | 'operational' | 'marketing';
export type SmsMessageStatus = 'queued' | 'sent' | 'failed' | 'unknown';

export interface SmsCapability {
  type: SmsProviderType;
  label: string;
  available: boolean;
  requiresCredentials: boolean;
  environments: AccountEnvironment[];
  notes: string;
}

export interface SmsAccountInput {
  name: string;
  senderHeader: string;
  username: string | null;
  environment: AccountEnvironment;
  enabled: boolean;
  lowCreditThreshold: number;
  consoleUrl: string | null;
}

export interface SmsAccountCreate extends SmsAccountInput {
  providerType: SmsProviderType;
  password?: string | null;
  makeDefault?: boolean;
}

export interface SmsAccount extends SmsAccountInput {
  id: string;
  tenantId: string;
  projectId: string | null;
  providerType: SmsProviderType;
  hasSecret: boolean;
  isDefault: boolean;
  creditBalance: number;
  lowCredit: boolean;
  lastTestAt: string | null;
  lastTestOutcome: 'passed' | 'failed' | null;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface SmsCreditTransaction {
  id: string;
  kind: 'load' | 'consume' | 'refund' | 'adjust';
  quantity: number;
  balanceAfter: number;
  reason: string | null;
  messageId: string | null;
  createdBy: string;
  createdAt: string;
}

export interface SmsMessage {
  id: string;
  accountId: string;
  kind: string;
  purpose: SmsPurpose;
  typeCode: string | null;
  referenceType: string | null;
  referenceId: string | null;
  phoneMasked: string;
  segments: number;
  creditCost: number;
  status: SmsMessageStatus;
  providerType: SmsProviderType;
  providerMessageId: string | null;
  errorCode: string | null;
  correlationId: string | null;
  durationMs: number | null;
  createdBy: string;
  createdAt: string;
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

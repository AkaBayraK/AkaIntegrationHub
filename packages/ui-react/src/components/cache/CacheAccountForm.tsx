import { useState, type FormEvent } from 'react';
import type {
  CacheAccount,
  CacheAccountInput,
  CacheAuthMode,
  CacheLicenseInput,
  CacheLicenseType,
  CacheProviderType,
} from '../../api/types';
import { useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';
import { useHubClient } from '../../session';
import { safeConsoleUrl } from '../console/ConsolePanel';
import { Icon } from '../Icon';
import { ErrorNotice, Field } from '../smtp/shared';

interface LicenseState {
  type: CacheLicenseType;
  holder: string;
  reference: string;
  expiresOn: string;
  key: string;
  acknowledged: boolean;
}
type FormState = Omit<CacheAccountInput, 'license'> & {
  providerType: CacheProviderType;
  password: string;
  makeDefault: boolean;
  license: LicenseState;
};
type Errors = Partial<Record<keyof FormState | 'licenseHolder' | 'licenseKey' | 'licenseAck', MessageKey>>;

const KEY_PREFIX = /^[A-Za-z0-9._:-]{1,120}$/;
const MAX_DATABASE_INDEX = 15;
export const LICENSE_TYPES: readonly CacheLicenseType[] = ['agpl-3.0', 'rsal-2.0', 'sspl-1.0', 'redis-enterprise', 'redis-cloud'];
const COMMERCIAL: ReadonlySet<CacheLicenseType> = new Set(['redis-enterprise', 'redis-cloud']);

const EMPTY_LICENSE: LicenseState = {
  type: 'agpl-3.0',
  holder: '',
  reference: '',
  expiresOn: '',
  key: '',
  acknowledged: false,
};

const EMPTY: FormState = {
  name: '',
  providerType: 'valkey',
  host: 'localhost',
  port: 6379,
  tlsEnabled: false,
  authMode: 'none',
  username: '',
  password: '',
  databaseIndex: 0,
  keyPrefix: '',
  environment: 'test',
  enabled: true,
  makeDefault: false,
  timeoutSeconds: 5,
  consoleUrl: '',
  license: EMPTY_LICENSE,
};

export function validateCacheForm(
  state: FormState,
  opts: { creating: boolean; hasSecret: boolean; hasLicenseKey?: boolean },
): Errors {
  const errors: Errors = {};
  if (!state.name.trim()) errors.name = 'smtp.form.error.required';
  if (!state.host.trim()) errors.host = 'smtp.form.error.required';
  if (!Number.isInteger(state.port) || state.port < 1 || state.port > 65535) errors.port = 'smtp.form.error.port';
  if (!Number.isInteger(state.databaseIndex) || state.databaseIndex < 0 || state.databaseIndex > MAX_DATABASE_INDEX) {
    errors.databaseIndex = 'cache.form.error.database';
  }
  if (state.keyPrefix?.trim() && !KEY_PREFIX.test(state.keyPrefix.trim())) errors.keyPrefix = 'cache.form.error.prefix';
  if (state.environment === 'production' && state.authMode === 'none') errors.authMode = 'cache.form.error.prodAuth';
  if (state.authMode === 'acl' && !state.username?.trim()) errors.username = 'smtp.form.error.required';
  if (state.authMode !== 'none' && !state.password && (opts.creating || !opts.hasSecret)) {
    errors.password = 'smtp.form.error.required';
  }
  if (state.consoleUrl?.trim() && !safeConsoleUrl(state.consoleUrl.trim())) errors.consoleUrl = 'console.error.url';
  if (state.providerType === 'redis') Object.assign(errors, validateLicense(state.license, Boolean(opts.hasLicenseKey)));
  return errors;
}

type LicenseErrors = Partial<Record<'licenseHolder' | 'licenseKey' | 'licenseAck', MessageKey>>;

function validateLicense(license: LicenseState, hasStoredKey: boolean): LicenseErrors {
  const errors: LicenseErrors = {};
  const commercial = COMMERCIAL.has(license.type);
  if (commercial && !license.holder.trim()) errors.licenseHolder = 'smtp.form.error.required';
  if (commercial && !license.key && !hasStoredKey) errors.licenseKey = 'smtp.form.error.required';
  if (!license.acknowledged) errors.licenseAck = 'license.error.ack';
  return errors;
}

function toState(account: CacheAccount | null): FormState {
  if (!account) return EMPTY;
  const license = account.license;
  return {
    ...EMPTY,
    ...account,
    username: account.username ?? '',
    keyPrefix: account.keyPrefix ?? '',
    consoleUrl: account.consoleUrl ?? '',
    password: '',
    makeDefault: account.isDefault,
    license: license
      ? {
          type: license.type,
          holder: license.holder ?? '',
          reference: license.reference ?? '',
          expiresOn: license.expiresOn ?? '',
          key: '',
          acknowledged: false,
        }
      : EMPTY_LICENSE,
  };
}

function toLicense(state: FormState): CacheLicenseInput | null {
  if (state.providerType !== 'redis') return null;
  const { license } = state;
  return {
    type: license.type,
    holder: license.holder.trim() || null,
    reference: license.reference.trim() || null,
    expiresOn: license.expiresOn || null,
    key: COMMERCIAL.has(license.type) && license.key ? license.key : null,
    acknowledged: license.acknowledged,
  };
}

function toInput(state: FormState): CacheAccountInput {
  return {
    name: state.name.trim(),
    host: state.host.trim(),
    port: state.port,
    tlsEnabled: state.tlsEnabled,
    authMode: state.authMode,
    username: state.authMode === 'acl' ? state.username?.trim() || null : null,
    databaseIndex: state.databaseIndex,
    keyPrefix: state.keyPrefix?.trim() || null,
    environment: state.environment,
    enabled: state.enabled,
    timeoutSeconds: state.timeoutSeconds,
    consoleUrl: state.consoleUrl?.trim() || null,
    license: toLicense(state),
  };
}

export function CacheAccountForm({
  tenantId,
  account,
  onSaved,
  onCancel,
}: {
  tenantId: string;
  account: CacheAccount | null;
  onSaved: (account: CacheAccount) => void;
  onCancel: () => void;
}) {
  const t = useTranslation();
  const client = useHubClient();
  const creating = account === null;
  const [state, setState] = useState<FormState>(() => toState(account));
  const [errors, setErrors] = useState<Errors>({});
  const [saving, setSaving] = useState(false);
  const [submitError, setSubmitError] = useState<unknown>(null);

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setState((prev) => ({ ...prev, [key]: value }));
  }

  async function save(): Promise<CacheAccount> {
    const body = toInput(state);
    const password = state.authMode === 'none' ? undefined : state.password || undefined;
    if (!account) {
      return client.createCacheAccount(tenantId, {
        ...body,
        providerType: state.providerType,
        password: password ?? null,
        makeDefault: state.makeDefault,
      });
    }
    const saved = await client.updateCacheAccount(tenantId, account.id, account.version, { ...body, password });
    if (state.makeDefault && !saved.isDefault && saved.enabled) {
      return client.makeDefaultCacheAccount(tenantId, saved.id, saved.version);
    }
    return saved;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = validateCacheForm(state, {
      creating,
      hasSecret: Boolean(account?.hasSecret),
      hasLicenseKey: Boolean(account?.license?.hasKey),
    });
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length > 0) return;
    setSaving(true);
    try {
      onSaved(await save());
    } catch (err) {
      setSubmitError(err);
    } finally {
      setSaving(false);
    }
  }

  const err = (key: keyof FormState) => (errors[key] ? t(errors[key]) : undefined);
  const authModes: CacheAuthMode[] = ['none', 'password', 'acl'];

  return (
    <form className="aih-surface aih-detail aih-form" onSubmit={(event) => void submit(event)} noValidate>
      <h2>{t(creating ? 'cache.form.createTitle' : 'cache.form.editTitle')}</h2>
      <div className="aih-grid-3">
        <Field id="aih-cache-name" label={t('cache.form.name')} error={err('name')}>
          <input
            id="aih-cache-name"
            className="aih-input"
            value={state.name}
            maxLength={120}
            onChange={(e) => set('name', e.target.value)}
          />
        </Field>
        <Field id="aih-cache-provider" label={t('cache.form.provider')}>
          <select
            id="aih-cache-provider"
            className="aih-select"
            value={state.providerType}
            disabled={!creating}
            onChange={(e) => set('providerType', e.target.value as CacheProviderType)}
          >
            <option value="valkey">Valkey</option>
            <option value="redis">{t('cache.provider.redis')}</option>
          </select>
        </Field>
        <Field id="aih-cache-environment" label={t('smtp.form.environment')}>
          <select
            id="aih-cache-environment"
            className="aih-select"
            value={state.environment}
            onChange={(e) => set('environment', e.target.value as FormState['environment'])}
          >
            <option value="test">{t('smtp.env.test')}</option>
            <option value="production">{t('smtp.env.production')}</option>
          </select>
        </Field>
      </div>
      {state.providerType === 'redis' && (
        <LicenseFieldset
          license={state.license}
          errors={errors}
          storedKey={Boolean(account?.license?.hasKey)}
          onChange={(license) => set('license', license)}
        />
      )}
      <div className="aih-grid-3">
        <Field id="aih-cache-host" label={t('smtp.form.host')} error={err('host')}>
          <input id="aih-cache-host" className="aih-input" value={state.host} onChange={(e) => set('host', e.target.value)} />
        </Field>
        <Field id="aih-cache-port" label={t('smtp.form.port')} error={err('port')}>
          <input
            id="aih-cache-port"
            className="aih-input"
            type="number"
            value={state.port}
            onChange={(e) => set('port', Number(e.target.value))}
          />
        </Field>
        <Field id="aih-cache-db" label={t('cache.form.database')} error={err('databaseIndex')}>
          <input
            id="aih-cache-db"
            className="aih-input"
            type="number"
            min={0}
            max={MAX_DATABASE_INDEX}
            value={state.databaseIndex}
            onChange={(e) => set('databaseIndex', Number(e.target.value))}
          />
        </Field>
      </div>
      <div className="aih-grid-3">
        <Field id="aih-cache-auth" label={t('cache.form.auth')} error={err('authMode')}>
          <select
            id="aih-cache-auth"
            className="aih-select"
            value={state.authMode}
            onChange={(e) => set('authMode', e.target.value as CacheAuthMode)}
          >
            {authModes.map((mode) => (
              <option key={mode} value={mode}>
                {t(`cache.auth.${mode}` as const)}
              </option>
            ))}
          </select>
        </Field>
        {state.authMode === 'acl' && (
          <Field id="aih-cache-username" label={t('smtp.form.username')} error={err('username')}>
            <input
              id="aih-cache-username"
              className="aih-input"
              autoComplete="off"
              value={state.username ?? ''}
              onChange={(e) => set('username', e.target.value)}
            />
          </Field>
        )}
        {state.authMode !== 'none' && (
          <Field
            id="aih-cache-password"
            label={t('smtp.form.password')}
            error={err('password')}
            help={account?.hasSecret ? t('cache.form.passwordKeep') : undefined}
          >
            <input
              id="aih-cache-password"
              className="aih-input"
              type="password"
              autoComplete="new-password"
              value={state.password}
              onChange={(e) => set('password', e.target.value)}
            />
          </Field>
        )}
      </div>
      <div className="aih-grid-3">
        <Field id="aih-cache-prefix" label={t('cache.form.prefix')} error={err('keyPrefix')} help={t('cache.form.prefixHint')}>
          <input
            id="aih-cache-prefix"
            className="aih-input"
            placeholder="buildingflow:"
            value={state.keyPrefix ?? ''}
            onChange={(e) => set('keyPrefix', e.target.value)}
          />
        </Field>
        <Field id="aih-cache-timeout" label={t('smtp.form.timeout')}>
          <input
            id="aih-cache-timeout"
            className="aih-input"
            type="number"
            min={1}
            max={60}
            value={state.timeoutSeconds}
            onChange={(e) => set('timeoutSeconds', Number(e.target.value))}
          />
        </Field>
        <Field id="aih-cache-console" label={t('console.field')} error={err('consoleUrl')} help={t('console.fieldHint')}>
          <input
            id="aih-cache-console"
            className="aih-input"
            type="url"
            placeholder="https://cache-ui.example.com"
            value={state.consoleUrl ?? ''}
            onChange={(e) => set('consoleUrl', e.target.value)}
          />
        </Field>
      </div>
      <div className="aih-row aih-row--wrap">
        <label className="aih-check">
          <input type="checkbox" checked={state.tlsEnabled} onChange={(e) => set('tlsEnabled', e.target.checked)} />
          <span>{t('cache.form.tls')}</span>
        </label>
        <label className="aih-check">
          <input type="checkbox" checked={state.enabled} onChange={(e) => set('enabled', e.target.checked)} />
          <span>{t('smtp.form.enabled')}</span>
        </label>
        <label className="aih-check">
          <input
            type="checkbox"
            checked={state.makeDefault}
            disabled={!state.enabled || Boolean(account?.isDefault)}
            onChange={(e) => set('makeDefault', e.target.checked)}
          />
          <span>{t('smtp.form.makeDefault')}</span>
        </label>
      </div>
      {submitError !== null && <ErrorNotice error={submitError} />}
      <div className="aih-row">
        <button type="submit" className="aih-button aih-button--primary" disabled={saving}>
          {saving ? t('common.loading') : t('common.save')}
        </button>
        <button type="button" className="aih-button aih-button--ghost" onClick={onCancel} disabled={saving}>
          {t('common.cancel')}
        </button>
      </div>
    </form>
  );
}

function LicenseFieldset({
  license,
  errors,
  storedKey,
  onChange,
}: {
  license: LicenseState;
  errors: Errors;
  storedKey: boolean;
  onChange: (license: LicenseState) => void;
}) {
  const t = useTranslation();
  const commercial = COMMERCIAL.has(license.type);
  const update = <K extends keyof LicenseState>(key: K, value: LicenseState[K]) => onChange({ ...license, [key]: value });
  const err = (key: keyof Errors) => (errors[key] ? t(errors[key]) : undefined);
  return (
    <fieldset className="aih-license">
      <legend>
        <Icon name="shield" size={16} /> {t('license.title')}
      </legend>
      <p className="aih-notice">{t('cache.form.redisNote')}</p>
      <div className="aih-grid-3">
        <Field id="aih-license-type" label={t('license.type')} help={t(`license.typeHint.${license.type}` as const)}>
          <select
            id="aih-license-type"
            className="aih-select"
            value={license.type}
            onChange={(e) => update('type', e.target.value as CacheLicenseType)}
          >
            {LICENSE_TYPES.map((type) => (
              <option key={type} value={type}>
                {t(`license.type.${type}` as const)}
              </option>
            ))}
          </select>
        </Field>
        <Field id="aih-license-holder" label={t('license.holder')} error={err('licenseHolder')}>
          <input
            id="aih-license-holder"
            className="aih-input"
            maxLength={200}
            value={license.holder}
            onChange={(e) => update('holder', e.target.value)}
          />
        </Field>
        <Field id="aih-license-reference" label={t('license.reference')}>
          <input
            id="aih-license-reference"
            className="aih-input"
            maxLength={120}
            value={license.reference}
            onChange={(e) => update('reference', e.target.value)}
          />
        </Field>
        <Field id="aih-license-expires" label={t('license.expiresOn')}>
          <input
            id="aih-license-expires"
            className="aih-input"
            type="date"
            value={license.expiresOn}
            onChange={(e) => update('expiresOn', e.target.value)}
          />
        </Field>
        {commercial && (
          <Field
            id="aih-license-key"
            label={t('license.key')}
            error={err('licenseKey')}
            help={storedKey ? t('license.keyKeep') : undefined}
          >
            <input
              id="aih-license-key"
              className="aih-input"
              type="password"
              autoComplete="off"
              value={license.key}
              onChange={(e) => update('key', e.target.value)}
            />
          </Field>
        )}
      </div>
      <label className="aih-check">
        <input
          type="checkbox"
          checked={license.acknowledged}
          aria-invalid={Boolean(errors.licenseAck)}
          onChange={(e) => update('acknowledged', e.target.checked)}
        />
        <span>{t('license.acknowledge')}</span>
      </label>
      {errors.licenseAck && (
        <small className="aih-field__error" role="alert">
          {t(errors.licenseAck)}
        </small>
      )}
    </fieldset>
  );
}

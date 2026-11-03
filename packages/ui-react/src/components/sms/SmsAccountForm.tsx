import { useEffect, useState, type FormEvent } from 'react';
import type { AccountEnvironment, SmsAccount, SmsCapability, SmsProviderType } from '../../api/types';
import { useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';
import { useHubClient } from '../../session';
import { safeConsoleUrl } from '../console/ConsolePanel';
import { ErrorNotice, Field } from '../smtp/shared';

export interface SmsFormState {
  name: string;
  providerType: SmsProviderType;
  senderHeader: string;
  username: string;
  password: string;
  environment: AccountEnvironment;
  enabled: boolean;
  makeDefault: boolean;
  lowCreditThreshold: number;
  consoleUrl: string;
}

type Errors = Partial<Record<keyof SmsFormState, MessageKey>>;

const HEADER = /^[A-Za-z0-9 .-]{3,11}$/;
const MAX_CREDIT = 10_000_000;

const EMPTY: SmsFormState = {
  name: '',
  providerType: 'mock_test',
  senderHeader: '',
  username: '',
  password: '',
  environment: 'test',
  enabled: true,
  makeDefault: false,
  lowCreditThreshold: 100,
  consoleUrl: '',
};

export function validateSmsForm(
  state: SmsFormState,
  opts: { creating: boolean; hasSecret: boolean; requiresCredentials: boolean },
): Errors {
  const errors: Errors = {};
  if (!state.name.trim()) errors.name = 'smtp.form.error.required';
  if (!HEADER.test(state.senderHeader.trim())) errors.senderHeader = 'sms.form.error.header';
  if (!Number.isInteger(state.lowCreditThreshold) || state.lowCreditThreshold < 0 || state.lowCreditThreshold > MAX_CREDIT) {
    errors.lowCreditThreshold = 'sms.form.error.threshold';
  }
  if (opts.requiresCredentials && !state.username.trim()) errors.username = 'smtp.form.error.required';
  if (opts.requiresCredentials && !state.password && (opts.creating || !opts.hasSecret)) {
    errors.password = 'smtp.form.error.required';
  }
  if (state.consoleUrl.trim() && !safeConsoleUrl(state.consoleUrl.trim())) errors.consoleUrl = 'console.error.url';
  return errors;
}

function toState(account: SmsAccount | null): SmsFormState {
  if (!account) return EMPTY;
  return {
    ...EMPTY,
    ...account,
    username: account.username ?? '',
    consoleUrl: account.consoleUrl ?? '',
    password: '',
    makeDefault: account.isDefault,
  };
}

export function SmsAccountForm({
  tenantId,
  account,
  onSaved,
  onCancel,
}: {
  tenantId: string;
  account: SmsAccount | null;
  onSaved: (account: SmsAccount) => void;
  onCancel: () => void;
}) {
  const t = useTranslation();
  const client = useHubClient();
  const creating = account === null;
  const [capabilities, setCapabilities] = useState<SmsCapability[]>([]);
  const [state, setState] = useState<SmsFormState>(() => toState(account));
  const [errors, setErrors] = useState<Errors>({});
  const [saving, setSaving] = useState(false);
  const [submitError, setSubmitError] = useState<unknown>(null);

  useEffect(() => {
    client
      .smsCapabilities()
      .then(setCapabilities)
      .catch((err: unknown) => setSubmitError(err));
  }, [client]);

  const capability = capabilities.find((c) => c.type === state.providerType);
  const requiresCredentials = capability?.requiresCredentials ?? state.providerType !== 'mock_test';
  const environments: AccountEnvironment[] = capability?.environments ?? ['test', 'production'];

  function set<K extends keyof SmsFormState>(key: K, value: SmsFormState[K]) {
    setState((prev) => ({ ...prev, [key]: value }));
  }

  function changeProvider(type: SmsProviderType) {
    const next = capabilities.find((c) => c.type === type);
    setState((prev) => ({
      ...prev,
      providerType: type,
      environment: next && !next.environments.includes(prev.environment) ? (next.environments[0] ?? prev.environment) : prev.environment,
    }));
  }

  async function save(): Promise<SmsAccount> {
    const body = {
      name: state.name.trim(),
      senderHeader: state.senderHeader.trim(),
      username: requiresCredentials ? state.username.trim() || null : null,
      environment: state.environment,
      enabled: state.enabled,
      lowCreditThreshold: state.lowCreditThreshold,
      consoleUrl: state.consoleUrl.trim() || null,
    };
    const password = requiresCredentials && state.password ? state.password : undefined;
    if (!account) {
      return client.createSmsAccount(tenantId, {
        ...body,
        providerType: state.providerType,
        password: password ?? null,
        makeDefault: state.makeDefault,
      });
    }
    const saved = await client.updateSmsAccount(tenantId, account.id, account.version, { ...body, password });
    if (state.makeDefault && !saved.isDefault && saved.enabled) {
      return client.makeDefaultSmsAccount(tenantId, saved.id, saved.version);
    }
    return saved;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = validateSmsForm(state, { creating, hasSecret: Boolean(account?.hasSecret), requiresCredentials });
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

  const err = (key: keyof SmsFormState) => (errors[key] ? t(errors[key]) : undefined);

  return (
    <form className="aih-surface aih-detail aih-form" onSubmit={(event) => void submit(event)} noValidate>
      <h2>{t(creating ? 'sms.form.createTitle' : 'sms.form.editTitle')}</h2>
      <div className="aih-grid-3">
        <Field id="aih-sms-name" label={t('cache.form.name')} error={err('name')}>
          <input id="aih-sms-name" className="aih-input" maxLength={120} value={state.name} onChange={(e) => set('name', e.target.value)} />
        </Field>
        <Field id="aih-sms-provider" label={t('sms.form.provider')} help={capability?.notes}>
          <select
            id="aih-sms-provider"
            className="aih-select"
            value={state.providerType}
            disabled={!creating}
            onChange={(e) => changeProvider(e.target.value as SmsProviderType)}
          >
            {capabilities.map((c) => (
              <option key={c.type} value={c.type} disabled={!c.available}>
                {c.label}
                {c.available ? '' : ` — ${t('hub.soon')}`}
              </option>
            ))}
          </select>
        </Field>
        <Field id="aih-sms-environment" label={t('smtp.form.environment')}>
          <select
            id="aih-sms-environment"
            className="aih-select"
            value={state.environment}
            onChange={(e) => set('environment', e.target.value as AccountEnvironment)}
          >
            {environments.map((env) => (
              <option key={env} value={env}>
                {t(env === 'production' ? 'smtp.env.production' : 'smtp.env.test')}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <div className="aih-grid-3">
        <Field id="aih-sms-header" label={t('sms.form.header')} error={err('senderHeader')} help={t('sms.form.headerHint')}>
          <input
            id="aih-sms-header"
            className="aih-input"
            maxLength={11}
            placeholder="BLDFLOW"
            value={state.senderHeader}
            onChange={(e) => set('senderHeader', e.target.value)}
          />
        </Field>
        {requiresCredentials && (
          <Field id="aih-sms-username" label={t('sms.form.username')} error={err('username')}>
            <input
              id="aih-sms-username"
              className="aih-input"
              autoComplete="off"
              value={state.username}
              onChange={(e) => set('username', e.target.value)}
            />
          </Field>
        )}
        {requiresCredentials && (
          <Field
            id="aih-sms-password"
            label={t('sms.form.password')}
            error={err('password')}
            help={account?.hasSecret ? t('cache.form.passwordKeep') : undefined}
          >
            <input
              id="aih-sms-password"
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
        <Field id="aih-sms-threshold" label={t('sms.form.threshold')} error={err('lowCreditThreshold')}>
          <input
            id="aih-sms-threshold"
            className="aih-input"
            type="number"
            min={0}
            value={state.lowCreditThreshold}
            onChange={(e) => set('lowCreditThreshold', Number(e.target.value))}
          />
        </Field>
        <Field id="aih-sms-console" label={t('console.field')} error={err('consoleUrl')} help={t('console.fieldHint')}>
          <input
            id="aih-sms-console"
            className="aih-input"
            type="url"
            placeholder="https://portal.netgsm.com.tr"
            value={state.consoleUrl}
            onChange={(e) => set('consoleUrl', e.target.value)}
          />
        </Field>
      </div>
      <div className="aih-row aih-row--wrap">
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

import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { HubApiError } from '../../api/client';
import type {
  AccountEnvironment,
  AuthMode,
  ProviderType,
  SmtpAccount,
  SmtpAccountInput,
  SmtpCapability,
  TlsMode,
} from '../../api/types';
import { useAkaIntegration, useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';
import { useHubClient, useHubSession } from '../../session';
import { safeConsoleUrl } from '../console/ConsolePanel';
import { ErrorNotice, Field, SMTP_BASE_PATH } from './shared';

type FormState = SmtpAccountInput & { password: string; makeDefault: boolean };
type Errors = Partial<Record<keyof FormState, MessageKey | string>>;

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const EMPTY: FormState = {
  name: '',
  providerType: 'custom_smtp',
  host: '',
  port: 587,
  tlsMode: 'starttls',
  authMode: 'smtp_auth',
  username: '',
  password: '',
  senderAddress: '',
  senderName: '',
  replyTo: '',
  environment: 'production',
  enabled: true,
  makeDefault: false,
  priority: 100,
  timeoutSeconds: 15,
  rateLimitPerMinute: null,
  consoleUrl: null,
};

export function validateSmtpForm(state: FormState, opts: { creating: boolean; hasSecret: boolean }): Errors {
  const errors: Errors = {};
  if (!state.name.trim()) errors.name = 'smtp.form.error.required';
  if (!state.host.trim()) errors.host = 'smtp.form.error.required';
  if (!Number.isInteger(state.port) || state.port < 1 || state.port > 65535) errors.port = 'smtp.form.error.port';
  if (!EMAIL.test(state.senderAddress.trim())) errors.senderAddress = 'smtp.form.error.email';
  if (state.replyTo && !EMAIL.test(state.replyTo.trim())) errors.replyTo = 'smtp.form.error.email';
  if (state.consoleUrl?.trim() && !safeConsoleUrl(state.consoleUrl.trim())) errors.consoleUrl = 'console.error.url';
  if (state.environment === 'production' && state.tlsMode === 'none') errors.tlsMode = 'smtp.form.error.prodTls';
  if ((state.port === 587 && state.tlsMode === 'implicit') || (state.port === 465 && state.tlsMode === 'starttls')) {
    errors.port = 'smtp.form.error.portTls';
  }
  if (state.authMode === 'smtp_auth') {
    if (!state.username?.trim()) errors.username = 'smtp.form.error.required';
    if (!state.password && (opts.creating || !opts.hasSecret)) errors.password = 'smtp.form.error.required';
  }
  return errors;
}


export function SmtpAccountForm({ accountId, basePath = SMTP_BASE_PATH }: { accountId?: string; basePath?: string }) {
  const t = useTranslation();
  const { navigation } = useAkaIntegration();
  const client = useHubClient();
  const session = useHubSession();
  const tenantId = session.me?.tenant.id ?? null;
  const creating = !accountId;

  const [capabilities, setCapabilities] = useState<SmtpCapability[] | null>(null);
  const [account, setAccount] = useState<SmtpAccount | null>(null);
  const [state, setState] = useState<FormState>(EMPTY);
  const [errors, setErrors] = useState<Errors>({});
  const [submitError, setSubmitError] = useState<unknown>(null);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!tenantId) return;
    let cancelled = false;
    (async () => {
      try {
        const caps = await client.smtpCapabilities();
        if (cancelled) return;
        setCapabilities(caps);
        if (accountId) {
          const existing = await client.getSmtpAccount(tenantId, accountId);
          if (cancelled) return;
          setAccount(existing);
          setState({
            ...EMPTY,
            ...existing,
            username: existing.username ?? '',
            senderName: existing.senderName ?? '',
            replyTo: existing.replyTo ?? '',
            password: '',
            makeDefault: existing.isDefault,
          });
        }
      } catch (err) {
        if (!cancelled) setLoadError(err);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [client, tenantId, accountId]);

  const capability = useMemo(
    () => capabilities?.find((c) => c.type === state.providerType) ?? null,
    [capabilities, state.providerType],
  );

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setState((prev) => ({ ...prev, [key]: value }));
  }

  function changeProvider(type: ProviderType) {
    const cap = capabilities?.find((c) => c.type === type);
    setState((prev) => {
      const next = { ...prev, providerType: type };
      if (cap && creating) {
        next.host = cap.defaultHost ?? prev.host;
        next.port = cap.defaultPort;
        next.tlsMode = cap.defaultTls;
        next.authMode = cap.authModes[0] ?? 'none';
        if (!cap.environments.includes(prev.environment)) next.environment = cap.environments[0] ?? prev.environment;
      }
      return next;
    });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!tenantId) return;
    const found = validateSmtpForm(state, { creating, hasSecret: Boolean(account?.hasSecret) });
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length > 0) return;
    setSaving(true);
    const body: SmtpAccountInput = {
      name: state.name.trim(),
      providerType: state.providerType,
      host: state.host.trim(),
      port: state.port,
      tlsMode: state.tlsMode,
      authMode: state.authMode,
      username: state.authMode === 'smtp_auth' ? state.username?.trim() || null : null,
      senderAddress: state.senderAddress.trim(),
      senderName: state.senderName?.trim() || null,
      replyTo: state.replyTo?.trim() || null,
      environment: state.environment,
      enabled: state.enabled,
      priority: state.priority,
      timeoutSeconds: state.timeoutSeconds,
      rateLimitPerMinute: state.rateLimitPerMinute,
      consoleUrl: state.consoleUrl?.trim() || null,
    };
    try {
      if (creating) {
        await client.createSmtpAccount(tenantId, {
          ...body,
          password: state.authMode === 'smtp_auth' ? state.password : null,
          makeDefault: state.makeDefault,
        });
      } else if (account) {
        const { providerType: _ignored, ...changes } = body;
        let saved = await client.updateSmtpAccount(tenantId, account.id, account.version, changes);
        if (state.password && state.authMode === 'smtp_auth') {
          saved = await client.rotateSmtpSecret(tenantId, account.id, saved.version, state.password);
        }
        if (state.makeDefault && !saved.isDefault && saved.enabled) {
          await client.makeDefaultSmtpAccount(tenantId, account.id, saved.version);
        }
      }
      setState((prev) => ({ ...prev, password: '' }));
      navigation.navigate(basePath);
    } catch (err) {
      if (err instanceof HubApiError) {
        const fieldErrors: Errors = {};
        for (const e of err.problem.errors ?? []) fieldErrors[e.field as keyof FormState] = e.message;
        setErrors(fieldErrors);
      }
      setSubmitError(err);
    } finally {
      setSaving(false);
    }
  }

  if (session.loading || (!capabilities && !loadError)) return <p role="status">{t('common.loading')}</p>;
  if (loadError) return <ErrorNotice error={loadError} />;

  const err = (key: keyof FormState) => {
    const value = errors[key];
    if (!value) return undefined;
    return value.startsWith('smtp.') || value.startsWith('console.') ? t(value as MessageKey) : value;
  };
  const describe = (key: keyof FormState, help = false) =>
    [errors[key] ? `aih-smtp-${key}-error` : null, help ? `aih-smtp-${key}-help` : null].filter(Boolean).join(' ') ||
    undefined;
  const tlsModes: TlsMode[] = capability?.tlsModes ?? ['starttls', 'implicit', 'none'];
  const authModes: AuthMode[] = [...(capability?.authModes ?? []), ...(capability?.plannedAuthModes ?? [])];
  const environments: AccountEnvironment[] = capability?.environments ?? ['test', 'production'];
  const conflict = submitError instanceof HubApiError && submitError.status === 412;

  return (
    <div className="aih-page">
      <h1>{t(creating ? 'smtp.form.createTitle' : 'smtp.form.editTitle')}</h1>
      <form className="aih-form aih-card" onSubmit={submit} noValidate aria-busy={saving}>
        <fieldset>
          <legend>{t('smtp.form.section.connection')}</legend>
          <Field id="aih-smtp-name" label={t('smtp.form.name')} error={err('name')}>
            <input
              id="aih-smtp-name"
              className="aih-input"
              value={state.name}
              maxLength={120}
              required
              aria-invalid={Boolean(errors.name)}
              aria-describedby={describe('name')}
              onChange={(e) => set('name', e.target.value)}
            />
          </Field>
          <Field id="aih-smtp-providerType" label={t('smtp.form.providerType')} help={capability?.notes || undefined}>
            <select
              id="aih-smtp-providerType"
              className="aih-select"
              value={state.providerType}
              disabled={!creating}
              aria-describedby={capability?.notes ? 'aih-smtp-providerType-help' : undefined}
              onChange={(e) => changeProvider(e.target.value as ProviderType)}
            >
              {capabilities?.map((c) => (
                <option key={c.type} value={c.type}>
                  {c.label}
                </option>
              ))}
            </select>
          </Field>
          <div className="aih-grid-2">
            <Field id="aih-smtp-host" label={t('smtp.form.host')} error={err('host')}>
              <input
                id="aih-smtp-host"
                className="aih-input"
                value={state.host}
                autoComplete="off"
                spellCheck={false}
                required
                aria-invalid={Boolean(errors.host)}
                aria-describedby={describe('host')}
                onChange={(e) => set('host', e.target.value)}
              />
            </Field>
            <Field id="aih-smtp-port" label={t('smtp.form.port')} error={err('port')}>
              <input
                id="aih-smtp-port"
                className="aih-input"
                type="number"
                min={1}
                max={65535}
                value={state.port}
                aria-invalid={Boolean(errors.port)}
                aria-describedby={describe('port')}
                onChange={(e) => set('port', Number(e.target.value))}
              />
            </Field>
          </div>
          <Field id="aih-smtp-tlsMode" label={t('smtp.form.tlsMode')} error={err('tlsMode')}>
            <select
              id="aih-smtp-tlsMode"
              className="aih-select"
              value={state.tlsMode}
              aria-invalid={Boolean(errors.tlsMode)}
              aria-describedby={describe('tlsMode')}
              onChange={(e) => set('tlsMode', e.target.value as TlsMode)}
            >
              {tlsModes.map((mode) => (
                <option key={mode} value={mode}>
                  {t(`smtp.form.tls.${mode}` as MessageKey)}
                </option>
              ))}
            </select>
          </Field>
        </fieldset>

        <fieldset>
          <legend>{t('smtp.form.section.auth')}</legend>
          <Field
            id="aih-smtp-authMode"
            label={t('smtp.form.authMode')}
            error={err('authMode')}
            help={capability?.plannedAuthModes.length ? t('smtp.form.oauthPlanned') : undefined}
          >
            <select
              id="aih-smtp-authMode"
              className="aih-select"
              value={state.authMode}
              aria-describedby={describe('authMode', Boolean(capability?.plannedAuthModes.length))}
              onChange={(e) => set('authMode', e.target.value as AuthMode)}
            >
              {authModes.map((mode) => (
                <option key={mode} value={mode} disabled={capability?.plannedAuthModes.includes(mode)}>
                  {t(`smtp.form.auth.${mode}` as MessageKey)}
                </option>
              ))}
            </select>
          </Field>
          {state.authMode === 'smtp_auth' && (
            <div className="aih-grid-2">
              <Field id="aih-smtp-username" label={t('smtp.form.username')} error={err('username')}>
                <input
                  id="aih-smtp-username"
                  className="aih-input"
                  value={state.username ?? ''}
                  autoComplete="off"
                  spellCheck={false}
                  aria-invalid={Boolean(errors.username)}
                  aria-describedby={describe('username')}
                  onChange={(e) => set('username', e.target.value)}
                />
              </Field>
              <Field
                id="aih-smtp-password"
                label={t(creating ? 'smtp.form.password' : 'smtp.form.passwordNew')}
                error={err('password')}
                help={
                  <>
                    {account?.hasSecret ? `${t('smtp.form.passwordStored')} ` : ''}
                    {t('smtp.form.passwordHelp')}
                  </>
                }
              >
                <input
                  id="aih-smtp-password"
                  className="aih-input"
                  type="password"
                  autoComplete="new-password"
                  value={state.password}
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={describe('password', true)}
                  onChange={(e) => set('password', e.target.value)}
                />
              </Field>
            </div>
          )}
        </fieldset>

        <fieldset>
          <legend>{t('smtp.form.section.sender')}</legend>
          <div className="aih-grid-2">
            <Field id="aih-smtp-senderAddress" label={t('smtp.form.senderAddress')} error={err('senderAddress')}>
              <input
                id="aih-smtp-senderAddress"
                className="aih-input"
                type="email"
                value={state.senderAddress}
                required
                aria-invalid={Boolean(errors.senderAddress)}
                aria-describedby={describe('senderAddress')}
                onChange={(e) => set('senderAddress', e.target.value)}
              />
            </Field>
            <Field id="aih-smtp-senderName" label={t('smtp.form.senderName')}>
              <input
                id="aih-smtp-senderName"
                className="aih-input"
                value={state.senderName ?? ''}
                maxLength={200}
                onChange={(e) => set('senderName', e.target.value)}
              />
            </Field>
          </div>
          <Field id="aih-smtp-replyTo" label={t('smtp.form.replyTo')} error={err('replyTo')}>
            <input
              id="aih-smtp-replyTo"
              className="aih-input"
              type="email"
              value={state.replyTo ?? ''}
              aria-invalid={Boolean(errors.replyTo)}
              aria-describedby={describe('replyTo')}
              onChange={(e) => set('replyTo', e.target.value)}
            />
          </Field>
        </fieldset>

        <fieldset>
          <legend>{t('smtp.form.section.options')}</legend>
          <Field id="aih-smtp-environment" label={t('smtp.form.environment')} error={err('environment')}>
            <select
              id="aih-smtp-environment"
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
          <div className="aih-grid-3">
            <Field id="aih-smtp-priority" label={t('smtp.form.priority')}>
              <input
                id="aih-smtp-priority"
                className="aih-input"
                type="number"
                min={0}
                max={10000}
                value={state.priority}
                onChange={(e) => set('priority', Number(e.target.value))}
              />
            </Field>
            <Field id="aih-smtp-timeout" label={t('smtp.form.timeout')}>
              <input
                id="aih-smtp-timeout"
                className="aih-input"
                type="number"
                min={1}
                max={120}
                value={state.timeoutSeconds}
                onChange={(e) => set('timeoutSeconds', Number(e.target.value))}
              />
            </Field>
            <Field id="aih-smtp-rate" label={t('smtp.form.rateLimit')}>
              <input
                id="aih-smtp-rate"
                className="aih-input"
                type="number"
                min={1}
                value={state.rateLimitPerMinute ?? ''}
                onChange={(e) => set('rateLimitPerMinute', e.target.value ? Number(e.target.value) : null)}
              />
            </Field>
          </div>
          <Field id="aih-smtp-console" label={t('console.field')} error={err('consoleUrl')}>
            <input
              id="aih-smtp-console"
              className="aih-input"
              type="url"
              placeholder="http://localhost:28025"
              value={state.consoleUrl ?? ''}
              aria-invalid={Boolean(errors.consoleUrl)}
              aria-describedby={describe('consoleUrl')}
              onChange={(e) => set('consoleUrl', e.target.value)}
            />
          </Field>
          <p className="aih-notice">{t('console.fieldHint')}</p>
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
        </fieldset>

        {conflict ? (
          <p className="aih-alert aih-alert--danger" role="alert">
            {t('smtp.form.error.conflict')}
          </p>
        ) : (
          submitError !== null && <ErrorNotice error={submitError} />
        )}
        <div className="aih-row">
          <button type="submit" className="aih-button aih-button--primary" disabled={saving}>
            {saving ? t('common.loading') : t('common.save')}
          </button>
          <button
            type="button"
            className="aih-button aih-button--ghost"
            onClick={() => navigation.navigate(basePath)}
            disabled={saving}
          >
            {t('common.cancel')}
          </button>
        </div>
      </form>
    </div>
  );
}

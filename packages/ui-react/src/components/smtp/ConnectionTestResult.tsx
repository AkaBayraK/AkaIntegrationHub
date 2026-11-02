import type { ConnectionTest } from '../../api/types';
import { useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';
import { Badge } from './shared';

const STEP_KEYS: Record<string, MessageKey> = {
  dns: 'smtp.step.dns',
  tcp: 'smtp.step.tcp',
  greeting: 'smtp.step.greeting',
  tls: 'smtp.step.tls',
  auth: 'smtp.step.auth',
};

export function ConnectionTestResult({ result, onClose }: { result: ConnectionTest; onClose: () => void }) {
  const t = useTranslation();
  return (
    <section className="aih-panel" aria-labelledby={`aih-test-${result.id}`} aria-live="polite">
      <div className="aih-row aih-row--between">
        <h3 id={`aih-test-${result.id}`}>
          {t('smtp.testResult.title')}{' '}
          <Badge tone={result.outcome === 'passed' ? 'success' : 'danger'}>
            {t(result.outcome === 'passed' ? 'smtp.test.passed' : 'smtp.test.failed')}
          </Badge>
        </h3>
        <button type="button" className="aih-button aih-button--ghost" onClick={onClose}>
          {t('common.close')}
        </button>
      </div>
      <ol className="aih-steps">
        {result.steps.map((step) => (
          <li key={step.step} className={`aih-steps__item aih-steps__item--${step.outcome}`}>
            <span>{step.step in STEP_KEYS ? t(STEP_KEYS[step.step] as MessageKey) : step.step}</span>
            <span className="aih-muted">
              {step.durationMs} ms{step.errorCode ? ` · ${step.errorCode}` : ''}
            </span>
          </li>
        ))}
      </ol>
      {result.errorCode && (
        <p>
          <code>{result.errorCode}</code>
        </p>
      )}
      <p className="aih-notice">{t('smtp.testResult.note')}</p>
    </section>
  );
}

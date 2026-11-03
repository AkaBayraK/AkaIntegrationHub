import type { ConnectionTest } from '../../api/types';
import { useTranslation } from '../../context';
import { StepTimeline } from '../ui/Detail';
import { Badge } from './shared';

export function ConnectionTestResult({ result, onClose }: { result: ConnectionTest; onClose: () => void }) {
  const t = useTranslation();
  return (
    <section className="aih-panel aih-test" aria-labelledby={`aih-test-${result.id}`} aria-live="polite">
      <div className="aih-row aih-row--between">
        <h3 id={`aih-test-${result.id}`}>
          {t('smtp.testResult.title')}{' '}
          <Badge tone={result.outcome === 'passed' ? 'success' : 'danger'}>
            {t(result.outcome === 'passed' ? 'smtp.test.passed' : 'smtp.test.failed')}
          </Badge>{' '}
          <span className="aih-muted">{result.durationMs} ms</span>
        </h3>
        <button type="button" className="aih-button aih-button--ghost aih-button--sm" onClick={onClose}>
          {t('common.close')}
        </button>
      </div>
      <StepTimeline steps={result.steps} />
      {result.errorCode && (
        <p>
          <code>{result.errorCode}</code>
        </p>
      )}
      <p className="aih-notice">{t('smtp.testResult.note')}</p>
    </section>
  );
}

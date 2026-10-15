'use client';

import { useTranslation } from '@aka/integration-ui';
import type { SystemInfo } from './system-info';

export function Overview({ systemInfo }: { systemInfo: SystemInfo | null }) {
  const t = useTranslation();
  return (
    <>
      <h1>{t('overview.title')}</h1>
      <section className="aih-card" aria-labelledby="api-status">
        <h2 id="api-status">{t('overview.apiStatus')}</h2>
        <p role="status">{systemInfo ? t('overview.apiUp') : t('overview.apiDown')}</p>
        {systemInfo && (
          <dl>
            <dt>{t('overview.version')}</dt>
            <dd>{systemInfo.version}</dd>
            <dt>{t('overview.environment')}</dt>
            <dd>{systemInfo.environment}</dd>
          </dl>
        )}
      </section>
    </>
  );
}

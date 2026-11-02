'use client';

import { IntegrationsHome, useTranslation } from '@aka/integration-ui';
import type { SystemInfo } from './system-info';

export function Overview({ systemInfo }: { systemInfo: SystemInfo | null }) {
  const t = useTranslation();
  const apiStatus = (
    <span
      role="status"
      className={systemInfo ? 'aih-pill aih-pill--neutral' : 'aih-pill aih-pill--danger'}
      title={systemInfo ? `${t('overview.version')} ${systemInfo.version} · ${systemInfo.environment}` : undefined}
    >
      <span className="aih-pill__dot" aria-hidden="true" />
      {t('overview.apiStatus')}: {systemInfo ? t('overview.apiUp') : t('overview.apiDown')}
    </span>
  );
  return <IntegrationsHome headerExtra={apiStatus} />;
}

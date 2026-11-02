'use client';

import { IntegrationsHome, useTranslation } from '@aka/integration-ui';
import type { SystemInfo } from './system-info';

export function Overview({ systemInfo }: { systemInfo: SystemInfo | null }) {
  const t = useTranslation();
  return (
    <>
      {!systemInfo && (
        <p className="aih-alert aih-alert--danger" role="alert" style={{ marginBottom: 'var(--aih-space-4)' }}>
          {t('home.apiDown')}
        </p>
      )}
      <IntegrationsHome />
      {systemInfo && (
        <p className="aih-notice" style={{ marginTop: 'var(--aih-space-8)' }}>
          {t('overview.apiStatus')}: {t('overview.apiUp')} · {t('overview.version')} {systemInfo.version} ·{' '}
          {t('overview.environment')} {systemInfo.environment}
        </p>
      )}
    </>
  );
}

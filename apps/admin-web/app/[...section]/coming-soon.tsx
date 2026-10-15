'use client';

import { useTranslation } from '@aka/integration-ui';

export function ComingSoon() {
  const t = useTranslation();
  return <p className="aih-muted">{t('common.comingSoon')}</p>;
}

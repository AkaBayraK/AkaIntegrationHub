'use client';

import { SmtpAccountsPage } from '@aka/integration-ui';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function SmtpAccountsWithSelection() {
  const account = useSearchParams().get('account');
  return <SmtpAccountsPage initialAccountId={account} />;
}

export default function SmtpAccountsRoute() {
  return (
    <Suspense fallback={null}>
      <SmtpAccountsWithSelection />
    </Suspense>
  );
}

'use client';

import { SmtpAccountForm } from '@aka/integration-ui';
import { useParams } from 'next/navigation';

export default function EditSmtpAccountRoute() {
  const params = useParams<{ id: string }>();
  return <SmtpAccountForm accountId={params.id} />;
}

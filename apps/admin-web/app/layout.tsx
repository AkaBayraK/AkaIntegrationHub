import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '@aka/design-tokens/tokens.css';
import '@aka/integration-ui/styles.css';
import './globals.css';
import { AdminHost } from './admin-host';

export const metadata: Metadata = {
  title: 'Aka Integration Hub',
  description: 'Connect · Notify · Automate',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <body>
        <AdminHost>{children}</AdminHost>
      </body>
    </html>
  );
}

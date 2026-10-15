import { fireEvent, render, screen } from '@testing-library/react';
import { useState, type ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { AkaIntegrationProvider, type AkaIntegrationAdapters, type ThemeMode } from '../context';
import type { Locale } from '../i18n/messages';
import { AppShell } from './AppShell';
import { LoginShell } from './LoginShell';

function Host({ children, navigate = vi.fn(), signIn = vi.fn(), authenticated = true }: {
  children: ReactNode;
  navigate?: (path: string) => void;
  signIn?: () => void;
  authenticated?: boolean;
}) {
  const [locale, setLocale] = useState<Locale>('tr');
  const [mode, setMode] = useState<ThemeMode>('light');
  const adapters: AkaIntegrationAdapters = {
    auth: { isAuthenticated: authenticated, getAccessToken: async () => null, signIn, signOut: vi.fn() },
    locale: { locale, setLocale },
    theme: { mode, setMode },
    navigation: { currentPath: '/', navigate },
    tenant: { tenantId: null, projectId: null },
  };
  return (
    <AkaIntegrationProvider adapters={adapters}>
      <span data-testid="mode">{mode}</span>
      {children}
    </AkaIntegrationProvider>
  );
}

describe('AppShell', () => {
  it('renders Turkish navigation and switches to English', () => {
    render(<Host><AppShell>content</AppShell></Host>);

    expect(screen.getByRole('navigation', { name: 'Ana menü' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Genel Bakış' })).toHaveAttribute('aria-current', 'page');

    fireEvent.change(screen.getByLabelText('Dil'), { target: { value: 'en' } });

    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Overview' })).toBeInTheDocument();
  });

  it('toggles theme through the host adapter', () => {
    render(<Host><AppShell>content</AppShell></Host>);

    fireEvent.click(screen.getByRole('button', { name: 'Koyu temaya geç' }));

    expect(screen.getByTestId('mode')).toHaveTextContent('dark');
    expect(screen.getByRole('button', { name: 'Açık temaya geç' })).toBeInTheDocument();
  });

  it('delegates navigation to the host router', () => {
    const navigate = vi.fn();
    render(<Host navigate={navigate}><AppShell>content</AppShell></Host>);

    fireEvent.click(screen.getByRole('link', { name: 'Sağlayıcılar' }));

    expect(navigate).toHaveBeenCalledWith('/providers');
  });

  it('offers a skip link to the main content', () => {
    render(<Host><AppShell>content</AppShell></Host>);

    expect(screen.getByRole('link', { name: 'İçeriğe geç' })).toHaveAttribute('href', '#aih-main');
    expect(screen.getByRole('main')).toHaveAttribute('id', 'aih-main');
  });

  it('hides sign out when unauthenticated', () => {
    render(<Host authenticated={false}><AppShell>content</AppShell></Host>);

    expect(screen.queryByRole('button', { name: 'Çıkış yap' })).not.toBeInTheDocument();
  });
});

describe('LoginShell', () => {
  it('delegates sign in to the host auth adapter', () => {
    const signIn = vi.fn();
    render(<Host signIn={signIn} authenticated={false}><LoginShell /></Host>);

    fireEvent.click(screen.getByRole('button', { name: 'Giriş yap' }));

    expect(signIn).toHaveBeenCalledOnce();
  });
});

describe('useAkaIntegration', () => {
  it('fails fast outside the provider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    expect(() => render(<AppShell>content</AppShell>)).toThrow(/AkaIntegrationProvider/);
  });
});

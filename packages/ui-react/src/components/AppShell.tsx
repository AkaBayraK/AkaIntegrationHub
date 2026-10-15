import type { ReactNode } from 'react';
import { useAkaIntegration, useTranslation } from '../context';
import type { Locale, MessageKey } from '../i18n/messages';
import { LogoMark } from './LogoMark';

export interface NavItem {
  path: string;
  labelKey: MessageKey;
}

export const DEFAULT_NAV_ITEMS: readonly NavItem[] = [
  { path: '/', labelKey: 'nav.dashboard' },
  { path: '/providers', labelKey: 'nav.providers' },
  { path: '/notifications', labelKey: 'nav.notifications' },
  { path: '/settings', labelKey: 'nav.settings' },
];

const LOCALES: readonly Locale[] = ['tr', 'en'];

export function AppShell({ children, navItems = DEFAULT_NAV_ITEMS }: { children: ReactNode; navItems?: readonly NavItem[] }) {
  const { auth, locale, theme, navigation } = useAkaIntegration();
  const t = useTranslation();
  const nextTheme = theme.mode === 'dark' ? 'light' : 'dark';

  return (
    <div className="aih-shell">
      <a className="aih-skip-link" href="#aih-main">
        {t('shell.skipToContent')}
      </a>
      <header className="aih-shell__header">
        <div className="aih-shell__brand">
          <LogoMark size={28} />
          <span>{t('app.name')}</span>
        </div>
        <div className="aih-shell__actions">
          <label className="aih-field">
            <span className="aih-visually-hidden">{t('shell.locale.label')}</span>
            <select
              className="aih-select"
              value={locale.locale}
              onChange={(event) => locale.setLocale(event.target.value as Locale)}
            >
              {LOCALES.map((code) => (
                <option key={code} value={code}>
                  {code.toUpperCase()}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="aih-button aih-button--ghost"
            onClick={() => theme.setMode(nextTheme)}
          >
            {t(nextTheme === 'dark' ? 'shell.theme.toDark' : 'shell.theme.toLight')}
          </button>
          {auth.isAuthenticated && (
            <button type="button" className="aih-button aih-button--ghost" onClick={auth.signOut}>
              {t('shell.signOut')}
            </button>
          )}
        </div>
      </header>
      <div className="aih-shell__body">
        <nav className="aih-shell__nav" aria-label={t('shell.mainNavigation')}>
          <ul>
            {navItems.map((item) => {
              const active = navigation.currentPath === item.path;
              return (
                <li key={item.path}>
                  <a
                    href={item.path}
                    aria-current={active ? 'page' : undefined}
                    className={active ? 'aih-nav-link aih-nav-link--active' : 'aih-nav-link'}
                    onClick={(event) => {
                      event.preventDefault();
                      navigation.navigate(item.path);
                    }}
                  >
                    {t(item.labelKey)}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>
        <main id="aih-main" className="aih-shell__main" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}

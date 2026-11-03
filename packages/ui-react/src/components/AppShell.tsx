import type { ReactNode } from 'react';
import { useAkaIntegration, useTranslation } from '../context';
import type { Locale, MessageKey } from '../i18n/messages';
import { Icon, type IconName } from './Icon';
import { LogoMark } from './LogoMark';

export interface NavItem {
  path: string;
  labelKey: MessageKey;
  icon?: IconName;
}

export const DEFAULT_NAV_ITEMS: readonly NavItem[] = [
  { path: '/', labelKey: 'nav.dashboard', icon: 'home' },
  { path: '/admin/email/providers', labelKey: 'nav.emailProviders', icon: 'mail' },
  { path: '/admin/email/deliveries', labelKey: 'nav.emailDeliveries', icon: 'history' },
  { path: '/providers', labelKey: 'nav.providers', icon: 'layers' },
  { path: '/notifications', labelKey: 'nav.notifications', icon: 'bell' },
  { path: '/settings', labelKey: 'nav.settings', icon: 'settings' },
];

const LOCALES: readonly Locale[] = ['tr', 'en'];
const NOTIFICATIONS_PATH = '/notifications';

function isActive(currentPath: string, path: string): boolean {
  return currentPath === path || (path !== '/' && currentPath.startsWith(`${path}/`));
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');
}

export function AppShell({
  children,
  navItems = DEFAULT_NAV_ITEMS,
  headerExtra,
}: {
  children: ReactNode;
  navItems?: readonly NavItem[];
  /** Host uygulamaya dönüş bağlantısı gibi ek başlık içeriği. */
  headerExtra?: ReactNode;
}) {
  const { auth, locale, theme, navigation } = useAkaIntegration();
  const t = useTranslation();
  const railItems = navItems.filter((item) => item.icon);
  const go = (path: string) => (event: { preventDefault: () => void }) => {
    event.preventDefault();
    navigation.navigate(path);
  };

  return (
    <div className="aih-shell">
      <a className="aih-skip-link" href="#aih-main">
        {t('shell.skipToContent')}
      </a>
      <header className="aih-shell__header">
        <div className="aih-shell__brand aih-pill">
          <LogoMark size={28} />
          <span>{t('app.name')}</span>
        </div>
        {headerExtra && <div className="aih-shell__extra">{headerExtra}</div>}
        <nav className="aih-shell__tabs aih-pill" aria-label={t('shell.mainNavigation')}>
          <ul>
            {navItems.map((item) => {
              const active = isActive(navigation.currentPath, item.path);
              return (
                <li key={item.path}>
                  <a
                    href={item.path}
                    aria-current={active ? 'page' : undefined}
                    className={active ? 'aih-tab aih-tab--active' : 'aih-tab'}
                    onClick={go(item.path)}
                  >
                    {t(item.labelKey)}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="aih-shell__actions">
          <div className="aih-pill aih-shell__tools">
            <label className="aih-locale">
              <Icon name="globe" size={18} />
              <span className="aih-visually-hidden">{t('shell.locale.label')}</span>
              <select value={locale.locale} onChange={(event) => locale.setLocale(event.target.value as Locale)}>
                {LOCALES.map((code) => (
                  <option key={code} value={code}>
                    {code.toUpperCase()}
                  </option>
                ))}
              </select>
            </label>
            <a
              href={NOTIFICATIONS_PATH}
              className="aih-icon-button"
              aria-label={t('nav.notifications')}
              title={t('nav.notifications')}
              onClick={go(NOTIFICATIONS_PATH)}
            >
              <Icon name="bell" />
            </a>
          </div>
          {auth.isAuthenticated && (
            <div className="aih-pill aih-user">
              <span className="aih-user__avatar" aria-hidden>
                {initials(auth.displayName ?? '') || '•'}
              </span>
              <span className="aih-user__name">{auth.displayName ?? t('shell.user')}</span>
            </div>
          )}
        </div>
      </header>
      <div className="aih-shell__body">
        <aside className="aih-rail">
          <div className="aih-rail__group" role="group" aria-label={t('shell.theme.label')}>
            <button
              type="button"
              className="aih-icon-button"
              aria-pressed={theme.mode === 'light'}
              aria-label={t('shell.theme.toLight')}
              title={t('shell.theme.toLight')}
              onClick={() => theme.setMode('light')}
            >
              <Icon name="sun" />
            </button>
            <button
              type="button"
              className="aih-icon-button"
              aria-pressed={theme.mode === 'dark'}
              aria-label={t('shell.theme.toDark')}
              title={t('shell.theme.toDark')}
              onClick={() => theme.setMode('dark')}
            >
              <Icon name="moon" />
            </button>
          </div>
          {railItems.length > 0 && (
            <nav className="aih-rail__group aih-rail__nav" aria-label={t('shell.quickNavigation')}>
              {railItems.map((item) => {
                const active = isActive(navigation.currentPath, item.path);
                return (
                  <a
                    key={item.path}
                    href={item.path}
                    aria-current={active ? 'page' : undefined}
                    aria-label={t(item.labelKey)}
                    title={t(item.labelKey)}
                    className={active ? 'aih-icon-button aih-icon-button--active' : 'aih-icon-button'}
                    onClick={go(item.path)}
                  >
                    {item.icon && <Icon name={item.icon} />}
                  </a>
                );
              })}
            </nav>
          )}
          {auth.isAuthenticated && (
            <div className="aih-rail__group aih-rail__bottom">
              <button
                type="button"
                className="aih-icon-button"
                aria-label={t('shell.signOut')}
                title={t('shell.signOut')}
                onClick={auth.signOut}
              >
                <Icon name="logout" />
              </button>
            </div>
          )}
        </aside>
        <main id="aih-main" className="aih-shell__main" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}

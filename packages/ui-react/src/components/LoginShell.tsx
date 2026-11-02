import type { ReactNode } from 'react';
import { useAkaIntegration, useTranslation } from '../context';
import { LogoMark } from './LogoMark';

/** ``children`` verilirse varsayılan giriş düğmesinin yerine gösterilir (ör. kimlik sağlayıcı seçimi). */
export function LoginShell({ children, notice }: { children?: ReactNode; notice?: ReactNode } = {}) {
  const { auth } = useAkaIntegration();
  const t = useTranslation();

  return (
    <main className="aih-login">
      <section className="aih-card aih-login__card" aria-labelledby="aih-login-title">
        <LogoMark size={56} />
        <h1 id="aih-login-title">{t('login.title')}</h1>
        <p className="aih-muted">{t('login.description')}</p>
        {children ?? (
          <button type="button" className="aih-button aih-button--primary" onClick={auth.signIn}>
            {t('login.submit')}
          </button>
        )}
        <p className="aih-notice" role="note">
          {notice ?? t('login.devNotice')}
        </p>
      </section>
    </main>
  );
}

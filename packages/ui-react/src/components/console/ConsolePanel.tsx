import { useState } from 'react';
import { useTranslation } from '../../context';

export function safeConsoleUrl(value: string | null | undefined): URL | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:' ? url : null;
  } catch {
    return null;
  }
}

/** Sağlayıcının kendi yönetim arayüzü (ör. Mailpit): yeni sekmede ya da sayfa içinde açılır. */
export function ConsolePanel({ url, title }: { url: string | null; title: string }) {
  const t = useTranslation();
  const [embedded, setEmbedded] = useState(false);
  const safe = safeConsoleUrl(url);
  if (!safe) return null;
  return (
    <div className="aih-console">
      <div className="aih-console__head">
        <div>
          <h3>{t('console.title')}</h3>
          <code className="aih-muted">{safe.host}</code>
        </div>
        <div className="aih-row aih-row--wrap">
          <button
            type="button"
            className="aih-button aih-button--ghost aih-button--sm"
            aria-pressed={embedded}
            onClick={() => setEmbedded((value) => !value)}
          >
            {t(embedded ? 'console.hide' : 'console.embed')}
          </button>
          <a
            className="aih-button aih-button--primary aih-button--sm"
            href={safe.toString()}
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('console.open')} ↗
          </a>
        </div>
      </div>
      {embedded && (
        <>
          <iframe
            className="aih-console__frame"
            src={safe.toString()}
            title={`${t('console.title')}: ${title}`}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
            referrerPolicy="no-referrer"
          />
          <p className="aih-notice">{t('console.embedHint')}</p>
        </>
      )}
    </div>
  );
}

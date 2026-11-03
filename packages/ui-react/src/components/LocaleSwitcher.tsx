import { useEffect, useId, useRef, useState } from 'react';
import { useAkaIntegration, useTranslation } from '../context';
import type { Locale } from '../i18n/messages';

interface LocaleOption {
  code: Locale;
  name: string;
}

const DEFAULT_LOCALE: LocaleOption = { code: 'tr', name: 'Türkçe' };
const LOCALES: readonly LocaleOption[] = [DEFAULT_LOCALE, { code: 'en', name: 'English' }];

export function Flag({ locale, size = 20 }: { locale: Locale; size?: number }) {
  const clipId = useId();
  const height = Math.round((size * 2) / 3);
  return (
    <svg width={size} height={height} viewBox="0 0 30 20" aria-hidden focusable="false" className="aih-flag">
      <clipPath id={clipId}>
        <rect width="30" height="20" rx="3" />
      </clipPath>
      <g clipPath={`url(#${clipId})`}>
        {locale === 'tr' ? (
          <>
            <rect width="30" height="20" fill="#E30A17" />
            <circle cx="10.5" cy="10" r="5" fill="#fff" />
            <circle cx="11.75" cy="10" r="4" fill="#E30A17" />
            <polygon
              fill="#fff"
              points="15.4,10 17.09,9.41 17.13,7.62 18.21,9.05 19.92,8.53 18.9,10 19.92,11.47 18.21,10.95 17.13,12.38 17.09,10.59"
            />
          </>
        ) : (
          <>
            <rect width="30" height="20" fill="#012169" />
            <path d="M0 0l30 20M30 0L0 20" stroke="#fff" strokeWidth="4" />
            <path d="M0 0l30 20M30 0L0 20" stroke="#C8102E" strokeWidth="1.6" />
            <path d="M15 0v20M0 10h30" stroke="#fff" strokeWidth="6" />
            <path d="M15 0v20M0 10h30" stroke="#C8102E" strokeWidth="3.4" />
          </>
        )}
      </g>
    </svg>
  );
}

export function LocaleSwitcher() {
  const { locale } = useAkaIntegration();
  const t = useTranslation();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const current = LOCALES.find((item) => item.code === locale.locale) ?? DEFAULT_LOCALE;

  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutside = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', closeOnOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('mousedown', closeOnOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open]);

  return (
    <div className="aih-locale" ref={rootRef}>
      <button
        type="button"
        className="aih-locale__button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={`${t('shell.locale.label')}: ${current.name}`}
        onClick={() => setOpen((value) => !value)}
      >
        <Flag locale={current.code} />
        <span aria-hidden>{current.code.toUpperCase()}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" aria-hidden fill="none" stroke="currentColor" strokeWidth="2">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      {open && (
        <ul id={listId} role="listbox" className="aih-locale__menu" aria-label={t('shell.locale.label')}>
          {LOCALES.map((item) => (
            <li key={item.code} role="option" aria-selected={item.code === current.code}>
              <button
                type="button"
                lang={item.code}
                onClick={() => {
                  locale.setLocale(item.code);
                  setOpen(false);
                }}
              >
                <Flag locale={item.code} />
                <span>{item.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { useId } from 'react';

export function LogoMark({ size = 32, title }: { size?: number; title?: string }) {
  const gradientId = useId();
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <defs>
        <linearGradient id={gradientId} x1="8" y1="56" x2="56" y2="8" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="var(--aih-color-brand-blue)" />
          <stop offset="0.55" stopColor="var(--aih-color-brand-violet)" />
          <stop offset="1" stopColor="var(--aih-color-brand-turquoise)" />
        </linearGradient>
      </defs>
      <path
        d="M10 54 L28.5 12.5 a4 4 0 0 1 7 0 L54 54"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M19 41 C27 33 37 47 45 39" fill="none" stroke="var(--aih-color-brand-turquoise)" strokeWidth="6" strokeLinecap="round" />
    </svg>
  );
}

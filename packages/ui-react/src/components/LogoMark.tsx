import { useId } from 'react';

export function LogoMark({ size = 32, title }: { size?: number; title?: string }) {
  const gradientId = useId();
  const gradient = `url(#${gradientId})`;
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
        <linearGradient id={gradientId} x1="10" y1="54" x2="54" y2="10" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="var(--aih-color-brand-blue)" />
          <stop offset="0.55" stopColor="var(--aih-color-brand-violet)" />
          <stop offset="1" stopColor="var(--aih-color-brand-turquoise)" />
        </linearGradient>
      </defs>
      <g transform="translate(0 5)">
        <g stroke={gradient} strokeWidth="5" strokeLinecap="round">
          <path d="M32 32 L32 11" />
          <path d="M32 32 L13.5 43" />
          <path d="M32 32 L50.5 43" />
        </g>
        <circle cx="32" cy="32" r="9" fill={gradient} />
        <circle cx="32" cy="10" r="6" fill="var(--aih-color-brand-turquoise)" />
        <circle cx="13" cy="43.5" r="6" fill="var(--aih-color-brand-blue)" />
        <circle cx="51" cy="43.5" r="6" fill="var(--aih-color-brand-violet)" />
      </g>
    </svg>
  );
}

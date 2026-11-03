export type IconName =
  | 'home'
  | 'mail'
  | 'history'
  | 'layers'
  | 'bell'
  | 'settings'
  | 'sun'
  | 'moon'
  | 'logout'
  | 'type-email'
  | 'type-cache'
  | 'type-queue'
  | 'type-sms'
  | 'type-webhook'
  | 'type-push'
  | 'type-whatsapp'
  | 'type-storage';

const PATHS: Record<IconName, readonly string[]> = {
  home: ['M4 4h6v6H4z', 'M14 4h6v6h-6z', 'M4 14h6v6H4z', 'M14 14h6v6h-6z'],
  mail: ['M3 6h18v12H3z', 'm3 7 9 6 9-6'],
  history: ['M3 12a9 9 0 1 0 3-6.7', 'M3 4v5h5', 'M12 7v5l3 3'],
  layers: ['m12 3 9 5-9 5-9-5z', 'm3 13 9 5 9-5'],
  bell: ['M6 16V11a6 6 0 0 1 12 0v5l2 2H4z', 'M10 20a2 2 0 0 0 4 0'],
  settings: [
    'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
    'M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
  ],
  sun: [
    'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
    'M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4',
  ],
  moon: ['M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z'],
  logout: ['M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4', 'm16 17 5-5-5-5', 'M21 12H9'],
  'type-email': ['M4.5 5.5h15a1.5 1.5 0 0 1 1.5 1.5v10a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17V7a1.5 1.5 0 0 1 1.5-1.5z', 'm3.5 7 8.5 6 8.5-6'],
  'type-cache': ['M13 2.5 4.5 13.5H11l-1 8 8.5-11H12z'],
  'type-queue': ['M3.5 6.5h11', 'M3.5 12h11', 'M3.5 17.5h11', 'm17.5 9 3 3-3 3'],
  'type-sms': ['M20.5 11.5a8 8 0 0 1-11.7 7.1L3.5 20l1.4-4.6A8 8 0 1 1 20.5 11.5z', 'M8.5 11.5h.01', 'M12.5 11.5h.01', 'M16.5 11.5h.01'],
  'type-webhook': ['M14 3.5h6.5V10', 'M20.5 3.5 11 13', 'M18 13.5V19a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 19V7.5A1.5 1.5 0 0 1 5 6h5.5'],
  'type-push': ['M6 16v-5a6 6 0 0 1 9-5.2', 'M18 11v5l2 2H4l2-2', 'M10 21a2 2 0 0 0 4 0', 'M19 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4z'],
  'type-whatsapp': [
    'M20.5 11.5a8.5 8.5 0 0 1-12.6 7.4L3.5 20l1.2-4.2A8.5 8.5 0 1 1 20.5 11.5z',
    'M9 8.3c0 3.6 2.9 6.6 6.5 6.7l1.1-1.7-2-1.1-1 .9a4.2 4.2 0 0 1-2.4-2.4l.9-1-1.1-2z',
  ],
  'type-storage': ['M3.5 4.5h17v4.5h-17z', 'M5 9v9.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V9', 'M10 13h4'],
};

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      focusable="false"
    >
      {PATHS[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}

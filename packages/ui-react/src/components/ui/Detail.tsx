import type { ReactNode } from 'react';
import type { TestStep } from '../../api/types';
import { useTranslation } from '../../context';
import type { MessageKey } from '../../i18n/messages';
import { Icon, type IconName } from '../Icon';

/** Detay ekranının üst kartı: kimlik (ikon, ad, alt bilgi), durum rozetleri ve birincil eylemler. */
export function DetailHero({
  mark,
  title,
  titleId,
  subtitle,
  badges,
  actions,
}: {
  mark: ReactNode;
  title: string;
  titleId: string;
  subtitle: ReactNode;
  badges?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="aih-hero">
      <div className="aih-hero__identity">
        <span className="aih-hero__mark">{mark}</span>
        <div className="aih-hero__text">
          <h2 id={titleId}>{title}</h2>
          <p>{subtitle}</p>
          {badges && <div className="aih-hero__badges">{badges}</div>}
        </div>
      </div>
      {actions && <div className="aih-hero__actions">{actions}</div>}
    </header>
  );
}

export interface InfoItem {
  icon: IconName;
  label: string;
  value: ReactNode;
  mono?: boolean;
  tone?: 'success' | 'danger' | 'warning' | 'accent';
}

/** İkonlu bilgi kutuları: her alanın ne olduğu ikondan da anlaşılır. */
export function InfoTiles({ items, size = 'md', label }: { items: readonly InfoItem[]; size?: 'md' | 'lg'; label?: string }) {
  return (
    <dl className={`aih-tiles aih-tiles--${size}`} aria-label={label}>
      {items.map((item) => (
        <div key={item.label} className={item.tone ? `aih-tile aih-tile--${item.tone}` : 'aih-tile'}>
          <span className="aih-tile__icon" aria-hidden="true">
            <Icon name={item.icon} size={size === 'lg' ? 22 : 18} />
          </span>
          <div className="aih-tile__body">
            <dt>{item.label}</dt>
            <dd className={item.mono ? 'aih-tile__value aih-tile__value--mono' : 'aih-tile__value'}>{item.value}</dd>
          </div>
        </div>
      ))}
    </dl>
  );
}

export function SectionTitle({ icon, children, aside }: { icon: IconName; children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="aih-section-title">
      <h3>
        <span className="aih-section-title__icon" aria-hidden="true">
          <Icon name={icon} size={16} />
        </span>
        {children}
      </h3>
      {aside}
    </div>
  );
}

const STEP_META: Record<string, { icon: IconName; label: MessageKey }> = {
  dns: { icon: 'globe', label: 'step.dns' },
  tcp: { icon: 'plug', label: 'step.tcp' },
  connect: { icon: 'plug', label: 'step.connect' },
  greeting: { icon: 'message', label: 'step.greeting' },
  tls: { icon: 'lock', label: 'step.tls' },
  auth: { icon: 'key', label: 'step.auth' },
  select: { icon: 'database', label: 'step.select' },
  ping: { icon: 'activity', label: 'step.ping' },
  info: { icon: 'info', label: 'step.info' },
};

/** Bağlantı testi adımları: soldan sağa, her adımda ikon, sonuç işareti ve süre. */
export function StepTimeline({ steps }: { steps: readonly TestStep[] }) {
  const t = useTranslation();
  return (
    <ol className="aih-timeline">
      {steps.map((step) => {
        const meta = STEP_META[step.step];
        return (
          <li key={step.step} className={`aih-timeline__step aih-timeline__step--${step.outcome}`}>
            <span className="aih-timeline__icon" aria-hidden="true">
              <Icon name={meta?.icon ?? 'activity'} size={18} />
              <span className="aih-timeline__status">
                <Icon name={step.outcome === 'failed' ? 'x' : 'check'} size={10} />
              </span>
            </span>
            <span className="aih-timeline__label">{meta ? t(meta.label) : step.step}</span>
            <span className="aih-timeline__meta">
              {step.outcome === 'skipped' ? t('step.skipped') : `${step.durationMs} ms`}
            </span>
            {step.errorCode && <code className="aih-timeline__error">{step.errorCode}</code>}
          </li>
        );
      })}
    </ol>
  );
}

export function ActionButton({
  icon,
  label,
  onClick,
  variant = 'ghost',
  disabled,
  ariaLabel,
}: {
  icon: IconName;
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'ghost';
  disabled?: boolean;
  ariaLabel?: string;
}) {
  return (
    <button
      type="button"
      className={`aih-button aih-button--${variant} aih-button--icon`}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
    >
      <Icon name={icon} size={16} />
      <span>{label}</span>
    </button>
  );
}

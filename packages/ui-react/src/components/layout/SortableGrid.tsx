import { useCallback, useEffect, useMemo, useState, type DragEvent, type KeyboardEvent, type ReactNode } from 'react';
import { useTranslation } from '../../context';
import {
  CARD_SIZES,
  clearLayout,
  dropCard,
  isDefaultLayout,
  mergeLayout,
  readLayout,
  resizeCard,
  shiftCard,
  writeLayout,
  type CardLayout,
} from './grid-layout';

export interface CardLayoutState {
  layout: CardLayout[];
  apply: (next: CardLayout[]) => void;
  reset: () => void;
  isDefault: boolean;
}

function browserStorage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function useCardLayout(section: string, subject: string | null, ids: readonly string[]): CardLayoutState {
  const idsKey = ids.join('|');
  const stableIds = useMemo(() => (idsKey ? idsKey.split('|') : []), [idsKey]);
  const [layout, setLayout] = useState<CardLayout[]>(() => mergeLayout(null, stableIds));

  useEffect(() => {
    const storage = browserStorage();
    setLayout(storage && subject ? readLayout(storage, section, subject, stableIds) : mergeLayout(null, stableIds));
  }, [section, subject, stableIds]);

  const apply = useCallback(
    (next: CardLayout[]) => {
      setLayout(next);
      const storage = browserStorage();
      if (storage && subject) writeLayout(storage, section, subject, next);
    },
    [section, subject],
  );

  const reset = useCallback(() => {
    const storage = browserStorage();
    if (storage && subject) clearLayout(storage, section, subject);
    setLayout(mergeLayout(null, stableIds));
  }, [section, subject, stableIds]);

  return { layout, apply, reset, isDefault: isDefaultLayout(layout, stableIds) };
}

export interface SortableItem {
  id: string;
  title: string;
  node: ReactNode;
}

const ARROW_DELTA: Partial<Record<string, -1 | 1>> = { ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1 };

export function SortableGrid({
  state,
  items,
  editing,
  className,
}: {
  state: CardLayoutState;
  items: readonly SortableItem[];
  editing: boolean;
  className?: string;
}) {
  const t = useTranslation();
  const [grabbed, setGrabbed] = useState<string | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [target, setTarget] = useState<string | null>(null);
  const byId = new Map(items.map((item) => [item.id, item]));
  const shown = state.layout.filter((card) => byId.has(card.id));
  const visibleIds = shown.map((card) => card.id);

  const endDrag = () => {
    setGrabbed(null);
    setDragging(null);
    setTarget(null);
  };
  const over = (event: DragEvent<HTMLLIElement>, id: string) => {
    if (!dragging || dragging === id) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    setTarget(id);
  };
  const shift = (id: string, delta: -1 | 1) => state.apply(shiftCard(state.layout, id, delta, visibleIds));
  const onGripKey = (event: KeyboardEvent<HTMLButtonElement>, id: string) => {
    const delta = ARROW_DELTA[event.key];
    if (!delta) return;
    event.preventDefault();
    shift(id, delta);
  };

  const classes = ['aih-sortable', className, editing ? 'aih-sortable--editing' : ''].filter(Boolean).join(' ');
  return (
    <ul className={classes}>
      {shown.map((card, index) => {
        const item = byId.get(card.id);
        if (!item) return null;
        const cardClasses = [
          'aih-sortable__card',
          `aih-sortable__card--span-${card.size}`,
          dragging === card.id ? 'is-dragging' : '',
          target === card.id ? 'is-target' : '',
        ]
          .filter(Boolean)
          .join(' ');
        return (
          <li
            key={card.id}
            className={cardClasses}
            draggable={editing && grabbed === card.id}
            onDragStart={(event) => {
              event.dataTransfer.effectAllowed = 'move';
              event.dataTransfer.setData('text/plain', card.id);
              setDragging(card.id);
            }}
            onDragEnd={endDrag}
            onDragOver={(event) => over(event, card.id)}
            onDragLeave={() => setTarget((current) => (current === card.id ? null : current))}
            onDrop={(event) => {
              event.preventDefault();
              const source = event.dataTransfer.getData('text/plain');
              endDrag();
              if (source) state.apply(dropCard(state.layout, source, card.id));
            }}
          >
            {editing && (
              <div className="aih-sortable__tools" role="group" aria-label={`${t('layout.tools')}: ${item.title}`}>
                <button
                  type="button"
                  className="aih-sortable__grip"
                  aria-label={`${t('layout.move')}: ${item.title}`}
                  title={t('layout.moveHint')}
                  onPointerDown={() => setGrabbed(card.id)}
                  onPointerUp={() => setGrabbed(null)}
                  onKeyDown={(event) => onGripKey(event, card.id)}
                >
                  <svg viewBox="0 0 24 24" aria-hidden fill="currentColor">
                    <circle cx="9" cy="6" r="1.6" />
                    <circle cx="15" cy="6" r="1.6" />
                    <circle cx="9" cy="12" r="1.6" />
                    <circle cx="15" cy="12" r="1.6" />
                    <circle cx="9" cy="18" r="1.6" />
                    <circle cx="15" cy="18" r="1.6" />
                  </svg>
                </button>
                <button
                  type="button"
                  disabled={index === 0}
                  aria-label={`${t('layout.earlier')}: ${item.title}`}
                  title={t('layout.earlier')}
                  onClick={() => shift(card.id, -1)}
                >
                  ‹
                </button>
                <button
                  type="button"
                  disabled={index === shown.length - 1}
                  aria-label={`${t('layout.later')}: ${item.title}`}
                  title={t('layout.later')}
                  onClick={() => shift(card.id, 1)}
                >
                  ›
                </button>
                <span className="aih-sortable__sizes" role="radiogroup" aria-label={`${t('layout.size')}: ${item.title}`}>
                  {CARD_SIZES.map((size) => (
                    <button
                      key={size}
                      type="button"
                      role="radio"
                      aria-checked={card.size === size}
                      title={t(size === 1 ? 'layout.size.normal' : 'layout.size.wide')}
                      onClick={() => state.apply(resizeCard(state.layout, card.id, size))}
                    >
                      {size}×
                    </button>
                  ))}
                </span>
              </div>
            )}
            {item.node}
          </li>
        );
      })}
    </ul>
  );
}

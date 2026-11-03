/** Kişiye özel kart düzeni (BuildingFlow dashboard ile aynı davranış): sıra ve genişlik tarayıcıda saklanır. */
export const CARD_SIZES = [1, 2] as const;
export type CardSize = (typeof CARD_SIZES)[number];

export interface CardLayout {
  id: string;
  size: CardSize;
}

const isSize = (value: unknown): value is CardSize => CARD_SIZES.includes(value as CardSize);

/** Kayıtlı düzeni güncel kart listesiyle birleştirir: artık olmayan kart düşer, yeni kart sona eklenir. */
export function mergeLayout(saved: unknown, ids: readonly string[]): CardLayout[] {
  const known: CardLayout[] = [];
  const seen = new Set<string>();
  if (Array.isArray(saved)) {
    for (const item of saved) {
      if (!item || typeof item !== 'object') continue;
      const { id, size } = item as Record<string, unknown>;
      if (typeof id !== 'string' || !ids.includes(id) || seen.has(id)) continue;
      seen.add(id);
      known.push({ id, size: isSize(size) ? size : 1 });
    }
  }
  return [...known, ...ids.filter((id) => !seen.has(id)).map((id) => ({ id, size: 1 as CardSize }))];
}

export const isDefaultLayout = (layout: readonly CardLayout[], ids: readonly string[]) =>
  layout.length === ids.length && layout.every((card, index) => card.id === ids[index] && card.size === 1);

/** İleri taşımada kart hedefin yerine geçer, geri taşımada hedefin önüne girer. */
export function dropCard(layout: readonly CardLayout[], source: string, target: string): CardLayout[] {
  const from = layout.findIndex((card) => card.id === source);
  const to = layout.findIndex((card) => card.id === target);
  const moving = layout[from];
  if (!moving || to < 0 || from === to) return [...layout];
  const next = layout.filter((card) => card.id !== source);
  const at = next.findIndex((card) => card.id === target);
  next.splice(from < to ? at + 1 : at, 0, moving);
  return next;
}

/** Klavye/dokunmatik taşıma: yalnız ekranda görünen kartlar arasında bir adım. */
export function shiftCard(
  layout: readonly CardLayout[],
  id: string,
  delta: -1 | 1,
  visible: readonly string[],
): CardLayout[] {
  const neighbour = visible[visible.indexOf(id) + delta];
  return visible.includes(id) && neighbour ? dropCard(layout, id, neighbour) : [...layout];
}

export const resizeCard = (layout: readonly CardLayout[], id: string, size: CardSize) =>
  layout.map((card) => (card.id === id ? { ...card, size } : card));

const storageKey = (section: string, subject: string) => `aih.layout.${section}.${subject}`;

// Gizli sekmede depolama hata atabilir; düzen kritik veri değildir, okunamazsa varsayılanla devam edilir.
export function readLayout(storage: Pick<Storage, 'getItem'>, section: string, subject: string, ids: readonly string[]) {
  try {
    const raw = storage.getItem(storageKey(section, subject));
    return mergeLayout(raw ? JSON.parse(raw) : null, ids);
  } catch {
    return mergeLayout(null, ids);
  }
}

export function writeLayout(
  storage: Pick<Storage, 'setItem'>,
  section: string,
  subject: string,
  layout: readonly CardLayout[],
): void {
  try {
    storage.setItem(storageKey(section, subject), JSON.stringify(layout));
  } catch {
    // Kaydedilemezse düzen yalnız bu oturumda geçerli kalır.
  }
}

export function clearLayout(storage: Pick<Storage, 'removeItem'>, section: string, subject: string): void {
  try {
    storage.removeItem(storageKey(section, subject));
  } catch {
    // Silinemezse varsayılana dönüş yine ekranda uygulanır.
  }
}

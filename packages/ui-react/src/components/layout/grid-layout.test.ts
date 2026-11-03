import { describe, expect, it } from 'vitest';
import { dropCard, isDefaultLayout, mergeLayout, readLayout, resizeCard, shiftCard, writeLayout } from './grid-layout';

const IDS = ['a', 'b', 'c', 'd'];

function memoryStorage(initial: Record<string, string> = {}) {
  const data = new Map(Object.entries(initial));
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => void data.set(key, value),
    data,
  };
}

describe('grid layout', () => {
  it('merges saved order, drops unknown cards and appends new ones', () => {
    const merged = mergeLayout([{ id: 'c', size: 2 }, { id: 'x', size: 1 }, { id: 'c', size: 1 }, { id: 'a', size: 9 }], IDS);

    expect(merged).toEqual([
      { id: 'c', size: 2 },
      { id: 'a', size: 1 },
      { id: 'b', size: 1 },
      { id: 'd', size: 1 },
    ]);
    expect(mergeLayout('bozuk', IDS).map((card) => card.id)).toEqual(IDS);
  });

  it('drops a card after a later target and before an earlier one', () => {
    const layout = mergeLayout(null, IDS);

    expect(dropCard(layout, 'a', 'c').map((card) => card.id)).toEqual(['b', 'c', 'a', 'd']);
    expect(dropCard(layout, 'd', 'b').map((card) => card.id)).toEqual(['a', 'd', 'b', 'c']);
    expect(dropCard(layout, 'a', 'a')).toEqual(layout);
  });

  it('shifts among visible cards only and stops at the edges', () => {
    const layout = mergeLayout(null, IDS);

    expect(shiftCard(layout, 'a', 1, ['a', 'c']).map((card) => card.id)).toEqual(['b', 'c', 'a', 'd']);
    expect(shiftCard(layout, 'a', -1, IDS)).toEqual(layout);
  });

  it('resizes and detects the default layout', () => {
    const layout = mergeLayout(null, IDS);

    expect(isDefaultLayout(layout, IDS)).toBe(true);
    expect(isDefaultLayout(resizeCard(layout, 'b', 2), IDS)).toBe(false);
  });

  it('persists per section and subject and survives broken storage', () => {
    const storage = memoryStorage();
    writeLayout(storage, 'hub-types', 'u1', dropCard(mergeLayout(null, IDS), 'd', 'a'));

    expect(readLayout(storage, 'hub-types', 'u1', IDS)[0]?.id).toBe('d');
    expect(readLayout(storage, 'hub-types', 'u2', IDS)[0]?.id).toBe('a');

    const broken = { getItem: () => { throw new Error('blocked'); } };
    expect(readLayout(broken, 'hub-types', 'u1', IDS).map((card) => card.id)).toEqual(IDS);
  });
});

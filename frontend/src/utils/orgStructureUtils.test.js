// src/utils/orgStructureUtils.test.js
import { findNodeInSubtree } from './orgStructureUtils';

describe('findNodeInSubtree', () => {
  const tree = {
    id: 1,
    name: 'Root',
    children: [
      {
        id: 2,
        name: 'Child 1',
        children: [
          { id: 3, name: 'Grandchild 1', children: [] },
          { org_unit_id: 4, name: 'Grandchild 2' },
        ],
      },
      { org_unit_id: 5, name: 'Child 2' },
    ],
  };

  test('возвращает true если targetId совпадает с id корня', () => {
    expect(findNodeInSubtree(tree, 1)).toBe(true);
  });

  test('возвращает true если targetId совпадает с id дочернего узла', () => {
    expect(findNodeInSubtree(tree, 3)).toBe(true);
  });

  test('возвращает true если targetId совпадает с org_unit_id дочернего узла', () => {
    expect(findNodeInSubtree(tree, 4)).toBe(true);
    expect(findNodeInSubtree(tree, 5)).toBe(true);
  });

  test('возвращает false если targetId отсутствует', () => {
    expect(findNodeInSubtree(tree, 999)).toBe(false);
  });

  test('возвращает false если children отсутствует', () => {
    const leaf = { id: 10, name: 'Leaf' };
    expect(findNodeInSubtree(leaf, 10)).toBe(true);
    expect(findNodeInSubtree(leaf, 999)).toBe(false);
  });
});

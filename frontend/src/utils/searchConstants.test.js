// src/constants/searchConstants.test.js
import { SEARCH_TYPES, SEARCH_TYPE_LABELS, INITIAL_FILTERS } from './searchConstants';

describe('searchConstants', () => {
  test('SEARCH_TYPES содержит правильные значения', () => {
    expect(SEARCH_TYPES.EMPLOYEE).toBe('employee');
    expect(SEARCH_TYPES.ORG_UNIT).toBe('org_unit');
  });

  test('SEARCH_TYPE_LABELS сопоставляет правильные лейблы', () => {
    expect(SEARCH_TYPE_LABELS[SEARCH_TYPES.EMPLOYEE]).toBe('Сотрудники');
    expect(SEARCH_TYPE_LABELS[SEARCH_TYPES.ORG_UNIT]).toBe('Орг.Единица');
  });

  test('INITIAL_FILTERS для EMPLOYEE содержит все поля с null', () => {
    const employeeFilters = INITIAL_FILTERS[SEARCH_TYPES.EMPLOYEE];
    expect(employeeFilters).toEqual({
      grade: null,
      skills: null,
      title: null,
      legalEntity: null,
    });
  });

  test('INITIAL_FILTERS для ORG_UNIT содержит все поля с null', () => {
    const orgUnitFilters = INITIAL_FILTERS[SEARCH_TYPES.ORG_UNIT];
    expect(orgUnitFilters).toEqual({
      domain: null,
      legalEntity: null,
      department: null,
      group: null,
    });
  });
});
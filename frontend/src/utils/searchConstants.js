export const SEARCH_TYPES = {
  EMPLOYEE: 'employee',
  ORG_UNIT: 'org_unit',
};

export const SEARCH_TYPE_LABELS = {
  [SEARCH_TYPES.EMPLOYEE]: 'Сотрудники',
  [SEARCH_TYPES.ORG_UNIT]: 'Орг.Единица',
};

export const INITIAL_FILTERS = {
  [SEARCH_TYPES.EMPLOYEE]: {
    grade: null,
    skills: null,
    title: null,
    legalEntity: null,
  },
  [SEARCH_TYPES.ORG_UNIT]: {
    domain: null,
    legalEntity: null,
    department: null,
    group: null,
  },
};
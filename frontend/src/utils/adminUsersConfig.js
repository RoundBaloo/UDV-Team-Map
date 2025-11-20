export const LEGAL_ENTITY_MAP = {
  'trinitydata': 'ТриниДата',
  'vneocheredi': 'ВНЕ ОЧЕРЕДИ', 
  'ft-soft': 'ФТ-СОФТ',
  'kit.ru': 'КИТ',
  'kit-r.ru': 'КИТ.Р',
  'cyberlimfa': 'Сайберлимфа',
  'vitrops': 'Витропс',
  'udv-group': 'UDV Group',
};

export const GRADE_OPTIONS = [
  { value: '', label: 'Не указан' },
  { value: 'Intern', label: 'Intern' },
  { value: 'Junior', label: 'Junior' },
  { value: 'Middle', label: 'Middle' },
  { value: 'Senior', label: 'Senior' },
  { value: 'Lead', label: 'Lead' },
  { value: 'Principal', label: 'Principal' },
];

export const WORK_FORMAT_OPTIONS = [
  { value: 'office', label: 'Офис' },
  { value: 'hybrid', label: 'Гибрид' },
  { value: 'remote', label: 'Удаленно' },
];

export const WORK_FORMAT_MAP = {
  office: 'Офис',
  hybrid: 'Гибрид',
  remote: 'Удаленно',
};

export const getLegalEntity = email => {
  if (!email) return '-';
  
  const domain = Object.keys(LEGAL_ENTITY_MAP).find(domain => 
    email.includes(domain)
  );
  
  return domain ? LEGAL_ENTITY_MAP[domain] : '-';
};
// src/utils/mockData.js

// Базовые моки сотрудников
export const mockEmployee = {
  id: 1,
  first_name: 'Иван',
  last_name: 'Иванов',
  middle_name: 'Иванович',
  email: 'ivanov@udv-group.ru',
  title: 'Разработчик',
  status: 'active',
  work_phone: '+7 (999) 123-45-67',
  mattermost_handle: '@ivanov',
  work_city: 'Москва',
  work_format: 'office',
  time_zone: 'Europe/Moscow',
  bio: 'Опытный разработчик с 5-летним стажем',
  hire_date: '2020-01-15',
  is_admin: false,
  is_blocked: false,
  last_login_at: '2024-01-15T10:30:00Z',
  photo: null,
  manager: null,
  org_unit: null,
};

export const mockCurrentUser = {
  ...mockEmployee,
  id: 2,
  first_name: 'Петр',
  last_name: 'Петров',
  email: 'petrov@udv-group.ru',
  title: 'Тимлид',
  is_admin: true,
};

export const mockTeam = {
  id: 27,
  name: 'Отдел разработки',
  description: 'Команда занимается разработкой веб-приложений',
  employee_count: 8,
  manager: {
    id: 2,
    first_name: 'Петр',
    last_name: 'Петров',
    title: 'Тимлид',
    photo: null,
  },
  members: [
    mockEmployee,
    {
      ...mockEmployee,
      id: 3,
      first_name: 'Мария',
      last_name: 'Сидорова',
      email: 'sidorova@udv-group.ru',
      title: 'Frontend разработчик',
    },
  ],
};

// Моки сотрудников для каждого конечного подразделения
// src/utils/mockData.js

export const mockEmployeesByUnit = {
  // UDV Digital Transformation
  4: [ // Основное подразделение (ТриниДата)
    {
      id: 1001,
      first_name: 'Алексей',
      last_name: 'Смирнов',
      title: 'Руководитель направления',
      email: 'smirnov@trinitydata.ru',
      is_manager: true,
    },
    {
      id: 1002,
      first_name: 'Ольга',
      last_name: 'Кузнецова',
      title: 'Старший аналитик',
      email: 'kuznetsova@trinitydata.ru',
    },
  ],
  6: [ // Основное подразделение (ВНЕ ОЧЕРЕДИ)
    {
      id: 1003,
      first_name: 'Сергей',
      last_name: 'Васильев',
      title: 'Руководитель проекта',
      email: 'vasiliev@vneocheredi.ru',
      is_manager: true,
    },
    {
      id: 1004,
      first_name: 'Екатерина',
      last_name: 'Новикова',
      title: 'Продуктовый дизайнер',
      email: 'novikova@vneocheredi.ru',
    },
  ],
  7: [ // Отдел продуктовой разработки (ВНЕ ОЧЕРЕДИ)
    {
      id: 1005,
      first_name: 'Андрей',
      last_name: 'Морозов',
      title: 'Lead Developer',
      email: 'morozov@vneocheredi.ru',
      is_manager: true,
    },
    {
      id: 1006,
      first_name: 'Наталья',
      last_name: 'Волкова',
      title: 'Backend разработчик',
      email: 'volkova@vneocheredi.ru',
    },
  ],
  9: [ // Администрация (ФТ-СОФТ)
    {
      id: 1007,
      first_name: 'Анна',
      last_name: 'Соколова',
      title: 'Директор по развитию',
      email: 'sokolova@ft-soft.ru',
      is_manager: true,
    },
  ],
  10: [ // Отдел продуктовой разработки 1 (ФТ-СОФТ)
    {
      id: 1008,
      first_name: 'Владимир',
      last_name: 'Орлов',
      title: 'Руководитель отдела',
      email: 'orlov@ft-soft.ru',
      is_manager: true,
    },
    {
      id: 1009,
      first_name: 'Татьяна',
      last_name: 'Андреева',
      title: 'Продуктовый менеджер',
      email: 'andreeva@ft-soft.ru',
    },
  ],
  11: [ // Отдел продуктовой разработки 2 (ФТ-СОФТ)
    {
      id: 1010,
      first_name: 'Денис',
      last_name: 'Павлов',
      title: 'Team Lead',
      email: 'pavlov@ft-soft.ru',
      is_manager: true,
    },
    {
      id: 1011,
      first_name: 'Ирина',
      last_name: 'Фролова',
      title: 'Frontend Developer',
      email: 'frolova@ft-soft.ru',
    },
  ],
  12: [ // Отдел заказной разработки (ФТ-СОФТ)
    {
      id: 1012,
      first_name: 'Максим',
      last_name: 'Власов',
      title: 'Руководитель отдела',
      email: 'vlasov@ft-soft.ru',
      is_manager: true,
    },
    {
      id: 1013,
      first_name: 'Любовь',
      last_name: 'Романова',
      title: 'Project Manager',
      email: 'romanova@ft-soft.ru',
    },
  ],
  14: [ // Направление аналитики и документации (ФТ-СОФТ)
    {
      id: 1014,
      first_name: 'Галина',
      last_name: 'Михайлова',
      title: 'Руководитель направления',
      email: 'mikhailova@ft-soft.ru',
      is_manager: true,
    },
    {
      id: 1015,
      first_name: 'Артур',
      last_name: 'Захаров',
      title: 'Технический писатель',
      email: 'zakharov@ft-soft.ru',
    },
  ],

  // UDV Security - КИТ
  17: [ // Администрация (КИТ)
    {
      id: 1016,
      first_name: 'Артем',
      last_name: 'Григорьев',
      title: 'Директор по безопасности',
      email: 'grigoriev@kit.ru',
      is_manager: true,
    },
  ],
  18: [ // Департамент консалтинга (КИТ)
    {
      id: 1017,
      first_name: 'Константин',
      last_name: 'Титов',
      title: 'Руководитель департамента',
      email: 'titov@kit.ru',
      is_manager: true,
    },
    {
      id: 1018,
      first_name: 'Елена',
      last_name: 'Федорова',
      title: 'Консультант по безопасности',
      email: 'fedorova@kit.ru',
    },
  ],
  19: [ // Отдел сопровождения информационных систем (КИТ)
    {
      id: 1019,
      first_name: 'Олег',
      last_name: 'Никитин',
      title: 'Руководитель отдела',
      email: 'nikitin@kit.ru',
      is_manager: true,
    },
    {
      id: 1020,
      first_name: 'Марина',
      last_name: 'Семенова',
      title: 'Системный администратор',
      email: 'semenova@kit.ru',
    },
  ],
  20: [ // Департамент по работе с иностранными заказчиками (КИТ)
    {
      id: 1021,
      first_name: 'Алина',
      last_name: 'Воробьева',
      title: 'Руководитель департамента',
      email: 'vorobyeva@kit.ru',
      is_manager: true,
    },
    {
      id: 1022,
      first_name: 'Руслан',
      last_name: 'Беляев',
      title: 'Менеджер по работе с клиентами',
      email: 'belyaev@kit.ru',
    },
  ],

  // UDV Security - КИТ.Р
  22: [ // Администрация (КИТ.Р)
    {
      id: 1023,
      first_name: 'Роман',
      last_name: 'Дмитриев',
      title: 'Технический директор',
      email: 'dmitriev@kit-r.ru',
      is_manager: true,
    },
  ],
  23: [ // Департамент разработки (КИТ.Р)
    {
      id: 1024,
      first_name: 'Георгий',
      last_name: 'Белов',
      title: 'Head of Development',
      email: 'belov@kit-r.ru',
      is_manager: true,
    },
    {
      id: 1025,
      first_name: 'Алиса',
      last_name: 'Ковалева',
      title: 'Senior Developer',
      email: 'kovaleva@kit-r.ru',
    },
  ],
  24: [ // Департамент кибербезопасности (КИТ.Р)
    {
      id: 1026,
      first_name: 'Станислав',
      last_name: 'Яковлев',
      title: 'Руководитель департамента',
      email: 'yakovlev@kit-r.ru',
      is_manager: true,
    },
    {
      id: 1027,
      first_name: 'Вероника',
      last_name: 'Гусева',
      title: 'Security Analyst',
      email: 'guseva@kit-r.ru',
    },
  ],
  25: [ // Департамент маркетинга (КИТ.Р)
    {
      id: 1028,
      first_name: 'Ксения',
      last_name: 'Тарасова',
      title: 'Marketing Director',
      email: 'tarasova@kit-r.ru',
      is_manager: true,
    },
    {
      id: 1029,
      first_name: 'Иван',
      last_name: 'Данилов',
      title: 'Marketing Specialist',
      email: 'danilov@kit-r.ru',
    },
  ],

  // UDV Security - Сайберлимфа
  27: [ // Администрация (Сайберлимфа)
    {
      id: 1030,
      first_name: 'Людмила',
      last_name: 'Павлова',
      title: 'Генеральный директор',
      email: 'pavlova@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  28: [ // Отдел персонала (Сайберлимфа)
    {
      id: 1031,
      first_name: 'Эдуард',
      last_name: 'Медведев',
      title: 'HR Manager',
      email: 'medvedev@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  29: [ // Отдел технического сопровождения (Сайберлимфа)
    {
      id: 1032,
      first_name: 'Никита',
      last_name: 'Зайцев',
      title: 'Руководитель отдела',
      email: 'zaitsev@cyberlimfa.ru',
      is_manager: true,
    },
    {
      id: 1033,
      first_name: 'Диана',
      last_name: 'Сорокина',
      title: 'Технический специалист',
      email: 'sorokina@cyberlimfa.ru',
    },
  ],
  30: [ // Отдел интеграции и автоматизации (Сайберлимфа)
    {
      id: 1034,
      first_name: 'Вадим',
      last_name: 'Кудрявцев',
      title: 'Integration Lead',
      email: 'kudryavtsev@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  31: [ // Отдел продуктового менеджмента (Сайберлимфа)
    {
      id: 1035,
      first_name: 'Арина',
      last_name: 'Семенова',
      title: 'Product Manager',
      email: 'semenova@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  33: [ // Группа серверной разработки (Сайберлимфа)
    {
      id: 1036,
      first_name: 'Глеб',
      last_name: 'Егоров',
      title: 'Backend Team Lead',
      email: 'egorov@cyberlimfa.ru',
      is_manager: true,
    },
    {
      id: 1037,
      first_name: 'Виктория',
      last_name: 'Крылова',
      title: 'Backend Developer',
      email: 'krylova@cyberlimfa.ru',
    },
  ],
  34: [ // Группа веб разработки (Сайберлимфа)
    {
      id: 1038,
      first_name: 'Дарья',
      last_name: 'Степанова',
      title: 'Frontend Team Lead',
      email: 'stepanova@cyberlimfa.ru',
      is_manager: true,
    },
    {
      id: 1039,
      first_name: 'Михаил',
      last_name: 'Филиппов',
      title: 'Frontend Developer',
      email: 'filippov@cyberlimfa.ru',
    },
  ],
  35: [ // Группа аналитики (Сайберлимфа)
    {
      id: 1040,
      first_name: 'София',
      last_name: 'Максимова',
      title: 'Lead Analyst',
      email: 'maximova@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  36: [ // Группа администрирования проектов (Сайберлимфа)
    {
      id: 1041,
      first_name: 'Тимур',
      last_name: 'Родионов',
      title: 'Project Administrator',
      email: 'rodionov@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  37: [ // Группа продуктового дизайна (Сайберлимфа)
    {
      id: 1042,
      first_name: 'Ангелина',
      last_name: 'Орлова',
      title: 'Lead Designer',
      email: 'orlova@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  39: [ // Отдел маркетинга (Сайберлимфа)
    {
      id: 1043,
      first_name: 'Марк',
      last_name: 'Соловьев',
      title: 'Marketing Manager',
      email: 'soloviev@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  40: [ // Отдел технической поддержки продаж (Сайберлимфа)
    {
      id: 1044,
      first_name: 'Юрий',
      last_name: 'Герасимов',
      title: 'Sales Support Lead',
      email: 'gerasimov@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  42: [ // Производственное направление (Сайберлимфа)
    {
      id: 1045,
      first_name: 'Валерий',
      last_name: 'Носков',
      title: 'Production Manager',
      email: 'noskov@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  43: [ // Аналитическое направление (Сайберлимфа)
    {
      id: 1046,
      first_name: 'Надежда',
      last_name: 'Виноградова',
      title: 'Analytics Lead',
      email: 'vinogradova@cyberlimfa.ru',
      is_manager: true,
    },
  ],
  44: [ // Отдел документирования и локализации (Сайберлимфа)
    {
      id: 1047,
      first_name: 'Сергей',
      last_name: 'Борисов',
      title: 'Documentation Manager',
      email: 'borisov@cyberlimfa.ru',
      is_manager: true,
    },
  ],

  // UDV Services - Витропс
  47: [ // Администрация (Витропс)
    {
      id: 1048,
      first_name: 'Лариса',
      last_name: 'Киселева',
      title: 'Генеральный директор',
      email: 'kiseleva@vitrops.ru',
      is_manager: true,
    },
  ],
  48: [ // Планово-экономический отдел (Витропс)
    {
      id: 1049,
      first_name: 'Анатолий',
      last_name: 'Громов',
      title: 'Начальник отдела',
      email: 'gromov@vitrops.ru',
      is_manager: true,
    },
  ],
  49: [ // Отдел поддержки 1С (Витропс)
    {
      id: 1050,
      first_name: 'Евгений',
      last_name: 'Тихонов',
      title: 'Руководитель поддержки',
      email: 'tikhonov@vitrops.ru',
      is_manager: true,
    },
    {
      id: 1051,
      first_name: 'Оксана',
      last_name: 'Жукова',
      title: 'Консультант 1С',
      email: 'zhukova@vitrops.ru',
    },
  ],
  50: [ // Отдел кадрового делопроизводства (Витропс)
    {
      id: 1052,
      first_name: 'Тамара',
      last_name: 'Прохорова',
      title: 'HR Specialist',
      email: 'prokhorova@vitrops.ru',
      is_manager: true,
    },
  ],
  51: [ // Юридический отдел (Витропс)
    {
      id: 1053,
      first_name: 'Григорий',
      last_name: 'Наумов',
      title: 'Юрист',
      email: 'naumov@vitrops.ru',
      is_manager: true,
    },
  ],
  52: [ // Служба внутреннего сервиса (Витропс)
    {
      id: 1054,
      first_name: 'Зоя',
      last_name: 'Потапова',
      title: 'Service Manager',
      email: 'potapova@vitrops.ru',
      is_manager: true,
    },
  ],
  53: [ // Отдел делопроизводства (Витропс)
    {
      id: 1055,
      first_name: 'Вячеслав',
      last_name: 'Мухин',
      title: 'Office Manager',
      email: 'mukhin@vitrops.ru',
      is_manager: true,
    },
  ],
  54: [ // Бухгалтерия (Витропс)
    {
      id: 1056,
      first_name: 'Лидия',
      last_name: 'Зуева',
      title: 'Главный бухгалтер',
      email: 'zueva@vitrops.ru',
      is_manager: true,
    },
    {
      id: 1057,
      first_name: 'Семен',
      last_name: 'Ширяев',
      title: 'Бухгалтер',
      email: 'shiryaev@vitrops.ru',
    },
  ],
};

// Функция для получения сотрудников подразделения
export const getEmployeesByUnitId = (unitId) => {
  return mockEmployeesByUnit[unitId] || [];
};

// Функция для получения руководителя подразделения
export const getManagerByUnitId = (unitId) => {
  const employees = getEmployeesByUnitId(unitId);
  return employees.find(emp => emp.is_manager) || null;
};

// Функция для получения участников подразделения (без руководителя)
export const getMembersByUnitId = (unitId) => {
  const employees = getEmployeesByUnitId(unitId);
  return employees.filter(emp => !emp.is_manager);
};

// Функция для получения количества сотрудников в подразделении
export const getEmployeeCountByUnitId = (unitId) => {
  return getEmployeesByUnitId(unitId).length;
};

// Структура организации (оставляем как было)
export const mockOrgStructure = {
  departments: [
    {
      id: 1,
      name: 'UDV Group',
      type: 'block',
      employee_count: 0,
      children: [
        // ... остальная структура без изменений
        // (полная структура из предыдущих сообщений)
      ],
    },
  ],
};
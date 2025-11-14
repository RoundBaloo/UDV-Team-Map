import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from './constants';

// Функция для поиска пути к узлу в дереве оргструктуры
export const findPathToNode = (node, targetId, path = []) => {
  // ИСПРАВЛЕНО: используем org_unit_id или id
  const nodeId = node.org_unit_id || node.id;
  const currentPath = [...path, { 
    id: nodeId, 
    name: node.name, 
    unit_type: node.unit_type,
  }];

  if (nodeId === targetId) {
    return currentPath;
  }

  if (node.children && node.children.length > 0) {
    for (let child of node.children) {
      const result = findPathToNode(child, targetId, currentPath);
      if (result) return result;
    }
  }

  return null;
};

// Форматирование имени сотрудника
export const formatEmployeeName = (firstName, lastName, middleName = '') => {
  const parts = [firstName, middleName, lastName].filter(Boolean);
  return parts.join(' ');
};

// Дебаунс функция для поиска
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Валидация email
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Проверка типа файла
export const isValidFileType = (file) => {
  return ALLOWED_FILE_TYPES.includes(file.type);
};

// Проверка размера файла  
export const isValidFileSize = (file) => {
  return file.size <= MAX_FILE_SIZE;
};

// Форматирование даты
export const formatDate = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('ru-RU');
};

// Обработка ошибок API
export const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  return error.message || 'Произошла ошибка';
};
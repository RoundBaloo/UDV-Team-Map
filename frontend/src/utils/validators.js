export const validators = {
  required: (value) => {
    if (!value || value.toString().trim() === '') {
      return 'Это поле обязательно для заполнения';
    }
    return null;
  },

  email: (value) => {
    if (!value) return null;
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return 'Введите корректный email адрес';
    }
    return null;
  },

  phone: (value) => {
    if (!value) return null;
    
    const phoneRegex = /^\+?[\d\s\-()]+$/;
    if (!phoneRegex.test(value.replace(/\s/g, ''))) {
      return 'Введите корректный номер телефона';
    }
    return null;
  },

  maxLength: (max) => (value) => {
    if (!value) return null;
    
    if (value.length > max) {
      return `Максимальная длина: ${max} символов`;
    }
    return null;
  },

  minLength: (min) => (value) => {
    if (!value) return null;
    
    if (value.length < min) {
      return `Минимальная длина: ${min} символов`;
    }
    return null;
  },
};

// Функция для композиции валидаторов
export const validate = (value, rules) => {
  for (const rule of rules) {
    const error = rule(value);
    if (error) return error;
  }
  return null;
};
// src/utils/validators.test.js
import { validators, validate } from './validators';

describe('validators', () => {
  describe('required', () => {
    test('возвращает ошибку если значение пустое', () => {
      expect(validators.required('')).toBe('Это поле обязательно для заполнения');
      expect(validators.required(null)).toBe('Это поле обязательно для заполнения');
      expect(validators.required(undefined)).toBe('Это поле обязательно для заполнения');
      expect(validators.required('   ')).toBe('Это поле обязательно для заполнения');
    });

    test('возвращает null если значение заполнено', () => {
      expect(validators.required('text')).toBeNull();
    });
  });

  describe('email', () => {
    test('возвращает null если значение пустое', () => {
      expect(validators.email('')).toBeNull();
      expect(validators.email(null)).toBeNull();
      expect(validators.email(undefined)).toBeNull();
    });

    test('валидные email', () => {
      expect(validators.email('test@example.com')).toBeNull();
      expect(validators.email('user.name+tag@domain.co')).toBeNull();
    });

    test('невалидные email', () => {
      expect(validators.email('not-an-email')).toBe('Введите корректный email адрес');
      expect(validators.email('test@')).toBe('Введите корректный email адрес');
      expect(validators.email('test@com')).toBe('Введите корректный email адрес');
    });
  });

  describe('phone', () => {
    test('возвращает null если значение пустое', () => {
      expect(validators.phone('')).toBeNull();
      expect(validators.phone(null)).toBeNull();
      expect(validators.phone(undefined)).toBeNull();
    });

    test('валидные номера телефонов', () => {
      expect(validators.phone('+7 999 123-45-67')).toBeNull();
      expect(validators.phone('8(999)1234567')).toBeNull();
      expect(validators.phone('9991234567')).toBeNull();
    });

    test('невалидные номера телефонов', () => {
      expect(validators.phone('abc')).toBe('Введите корректный номер телефона');
      expect(validators.phone('123abc')).toBe('Введите корректный номер телефона');
    });
  });

  describe('maxLength', () => {
    const rule = validators.maxLength(5);

    test('возвращает null если значение пустое', () => {
      expect(rule(null)).toBeNull();
      expect(rule(undefined)).toBeNull();
    });

    test('возвращает ошибку если длина больше максимума', () => {
      expect(rule('123456')).toBe('Максимальная длина: 5 символов');
    });

    test('возвращает null если длина в пределах максимума', () => {
      expect(rule('12345')).toBeNull();
      expect(rule('123')).toBeNull();
    });
  });

  describe('minLength', () => {
    const rule = validators.minLength(3);

    test('возвращает null если значение пустое', () => {
      expect(rule(null)).toBeNull();
      expect(rule(undefined)).toBeNull();
    });

    test('возвращает ошибку если длина меньше минимума', () => {
      expect(rule('12')).toBe('Минимальная длина: 3 символов');
    });

    test('возвращает null если длина соответствует минимуму', () => {
      expect(rule('123')).toBeNull();
      expect(rule('1234')).toBeNull();
    });
  });

  describe('validate', () => {
    test('возвращает первую ошибку из правил', () => {
      const rules = [validators.required, validators.minLength(5)];
      expect(validate('', rules)).toBe('Это поле обязательно для заполнения');
      expect(validate('123', rules)).toBe('Минимальная длина: 5 символов');
    });

    test('возвращает null если все правила пройдены', () => {
      const rules = [validators.required, validators.minLength(3), validators.maxLength(5)];
      expect(validate('123', rules)).toBeNull();
      expect(validate('12345', rules)).toBeNull();
    });
  });
});

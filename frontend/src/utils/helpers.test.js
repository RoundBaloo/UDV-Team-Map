// src/utils/helpers.test.js
import {
  findPathToNode,
  formatEmployeeName,
  debounce,
  isValidEmail,
  isValidFileType,
  isValidFileSize,
  formatDate,
  getErrorMessage
} from './helpers';
import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from './constants';

jest.useFakeTimers();

describe('utils', () => {
  describe('findPathToNode', () => {
    const tree = {
      id: 1,
      name: 'Root',
      unit_type: 'department',
      children: [
        { id: 2, name: 'Child 1', unit_type: 'team', children: [] },
        { org_unit_id: 3, name: 'Child 2', unit_type: 'team', children: [] },
      ],
    };

    test('находит путь до узла по id', () => {
      const path = findPathToNode(tree, 2);
      expect(path.map(n => n.id)).toEqual([1, 2]);
    });

    test('находит путь до узла по org_unit_id', () => {
      const path = findPathToNode(tree, 3);
      expect(path.map(n => n.id)).toEqual([1, 3]);
    });

    test('возвращает null если узел не найден', () => {
      expect(findPathToNode(tree, 999)).toBeNull();
    });
  });

  describe('formatEmployeeName', () => {
    test('собирает полное имя', () => {
      expect(formatEmployeeName('Ivan', 'Petrov', 'Sergeevich')).toBe('Ivan Sergeevich Petrov');
    });
    test('игнорирует пустое middleName', () => {
      expect(formatEmployeeName('Ivan', 'Petrov')).toBe('Ivan Petrov');
    });
  });

  describe('debounce', () => {
    test('вызывает функцию после задержки', () => {
      const fn = jest.fn();
      const debounced = debounce(fn, 100);
      debounced(1);
      debounced(2);
      expect(fn).not.toBeCalled();
      jest.advanceTimersByTime(100);
      expect(fn).toHaveBeenCalledWith(2);
    });
  });

  describe('isValidEmail', () => {
    test('валидные email', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
    });
    test('невалидные email', () => {
      expect(isValidEmail('not-an-email')).toBe(false);
    });
  });

  describe('isValidFileType', () => {
    test('валидный тип', () => {
      const file = { type: ALLOWED_FILE_TYPES[0] };
      expect(isValidFileType(file)).toBe(true);
    });
    test('невалидный тип', () => {
      const file = { type: 'application/pdf' };
      expect(isValidFileType(file)).toBe(false);
    });
  });

  describe('isValidFileSize', () => {
    test('меньше MAX_FILE_SIZE', () => {
      const file = { size: MAX_FILE_SIZE - 1 };
      expect(isValidFileSize(file)).toBe(true);
    });
    test('больше MAX_FILE_SIZE', () => {
      const file = { size: MAX_FILE_SIZE + 1 };
      expect(isValidFileSize(file)).toBe(false);
    });
  });

  describe('formatDate', () => {
    const dateStr = '2025-12-14T15:30:45Z';
    test('форматирует без времени', () => {
      expect(formatDate(dateStr)).toMatch(/\d{2}\.\d{2}\.\d{4}/);
    });
    test('форматирует с временем', () => {
      expect(formatDate(dateStr, true)).toMatch(/\d{2}\.\d{2}\.\d{4}/);
    });
    test('пустая строка если dateString пустой и includeTime=false', () => {
      expect(formatDate('', false)).toBe('');
    });
    test('возвращает "Никогда" если dateString пустой и includeTime=true', () => {
      expect(formatDate('', true)).toBe('Никогда');
    });
  });

  describe('getErrorMessage', () => {
    test('берет detail из error.response.data', () => {
      const error = { response: { data: { detail: 'Ошибка детали' } } };
      expect(getErrorMessage(error)).toBe('Ошибка детали');
    });
    test('берет error.message', () => {
      const error = { message: 'Some message' };
      expect(getErrorMessage(error)).toBe('Some message');
    });
    test('возвращает дефолт если нет message', () => {
      expect(getErrorMessage({})).toBe('Произошла ошибка');
    });
  });
});

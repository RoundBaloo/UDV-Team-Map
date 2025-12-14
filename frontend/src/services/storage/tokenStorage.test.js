// tokenStorage.test.js
import { tokenStorage } from './tokenStorage';

describe('tokenStorage', () => {
  const TOKEN_KEY = 'udv_access_token';

  beforeEach(() => {
    // Очистим localStorage и восстановим все шпионы/моки
    localStorage.clear();
    jest.restoreAllMocks();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('getToken возвращает токен из localStorage', () => {
    localStorage.setItem(TOKEN_KEY, 'abc123');
    expect(tokenStorage.getToken()).toBe('abc123');
  });

  test('getToken возвращает null если нет токена', () => {
    expect(tokenStorage.getToken()).toBeNull();
  });

  test('setToken сохраняет токен в localStorage', () => {
    tokenStorage.setToken('token456');
    expect(localStorage.getItem(TOKEN_KEY)).toBe('token456');
  });

  test('removeToken удаляет токен из localStorage', () => {
    localStorage.setItem(TOKEN_KEY, 'abc123');
    tokenStorage.removeToken();
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
  });

  test('hasToken возвращает true если токен есть', () => {
    localStorage.setItem(TOKEN_KEY, 'abc123');
    expect(tokenStorage.hasToken()).toBe(true);
  });

  test('hasToken возвращает false если токена нет', () => {
    localStorage.removeItem(TOKEN_KEY);
    expect(tokenStorage.hasToken()).toBe(false);
  });

  // ---- Тесты ошибок: используем spyOn на прототипе Storage ----

  test('getToken обрабатывает ошибки и логирует их', () => {
    const error = new Error('Storage error (getItem)');
    // Перехватываем вызовы getItem и заставляем их кидать
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw error;
    });

    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    const result = tokenStorage.getToken();

    expect(result).toBeNull();
    expect(consoleErrorSpy).toHaveBeenCalledWith('Error getting token from storage:', error);

    consoleErrorSpy.mockRestore();
  });

  test('setToken обрабатывает ошибки и логирует их', () => {
    const error = new Error('Storage error (setItem)');
    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw error;
    });

    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    // Не должно кидать исключение наружу
    expect(() => tokenStorage.setToken('abc')).not.toThrow();
    expect(consoleErrorSpy).toHaveBeenCalledWith('Error saving token to storage:', error);

    consoleErrorSpy.mockRestore();
  });

  test('removeToken обрабатывает ошибки и логирует их', () => {
    const error = new Error('Storage error (removeItem)');
    jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw error;
    });

    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => tokenStorage.removeToken()).not.toThrow();
    expect(consoleErrorSpy).toHaveBeenCalledWith('Error removing token from storage:', error);

    consoleErrorSpy.mockRestore();
  });

  // Проверки граничных значений для hasToken
  test('hasToken возвращает false когда токен пустая строка', () => {
    localStorage.setItem(TOKEN_KEY, '');
    expect(tokenStorage.hasToken()).toBe(false);
  });

  test('hasToken возвращает true когда getToken возвращает значение', () => {
    localStorage.setItem(TOKEN_KEY, 'test-token');
    expect(tokenStorage.hasToken()).toBe(true);
  });
});

import { tokenStorage } from './tokenStorage';

describe('tokenStorage', () => {
  const TOKEN_KEY = 'udv_access_token';

  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
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
    expect(tokenStorage.hasToken()).toBe(false);
  });

  test('getToken обрабатывает ошибки и логирует их', () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const orig = localStorage.getItem;
    const error = new Error('Storage error');
    localStorage.getItem = () => { throw error; };

    try {
      const result = tokenStorage.getToken();
      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error getting token from storage:', error);
    } finally {
      localStorage.getItem = orig;
      consoleErrorSpy.mockRestore();
    }
  });

  test('setToken обрабатывает ошибки и логирует их', () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const orig = localStorage.setItem;
    const error = new Error('Storage error');
    localStorage.setItem = () => { throw error; };

    try {
      expect(() => tokenStorage.setToken('abc')).not.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error saving token to storage:', error);
    } finally {
      localStorage.setItem = orig;
      consoleErrorSpy.mockRestore();
    }
  });

  test('removeToken обрабатывает ошибки и логирует их', () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const orig = localStorage.removeItem;
    const error = new Error('Storage error');
    localStorage.removeItem = () => { throw error; };

    try {
      expect(() => tokenStorage.removeToken()).not.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error removing token from storage:', error);
    } finally {
      localStorage.removeItem = orig;
      consoleErrorSpy.mockRestore();
    }
  });

  test('hasToken возвращает true когда getToken возвращает токен', () => {
    localStorage.setItem(TOKEN_KEY, 'test-token');
    expect(tokenStorage.hasToken()).toBe(true);
  });

  test('hasToken возвращает false когда getToken возвращает null', () => {
    localStorage.removeItem(TOKEN_KEY);
    expect(tokenStorage.hasToken()).toBe(false);
  });

  test('hasToken возвращает false когда getToken возвращает пустую строку', () => {
    localStorage.setItem(TOKEN_KEY, '');
    expect(tokenStorage.hasToken()).toBe(false);
  });
});

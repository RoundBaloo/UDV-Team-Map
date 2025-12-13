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

  test('getToken обрабатывает ошибки', () => {
    const orig = localStorage.getItem;
    localStorage.getItem = () => { throw new Error('fail'); };

    try {
      expect(tokenStorage.getToken()).toBeNull();
    } finally {
      localStorage.getItem = orig;
    }
  });

  test('setToken обрабатывает ошибки', () => {
    const orig = localStorage.setItem;
    localStorage.setItem = () => { throw new Error('fail'); };

    try {
      expect(() => tokenStorage.setToken('abc')).not.toThrow();
    } finally {
      localStorage.setItem = orig;
    }
  });

  test('removeToken обрабатывает ошибки', () => {
    const orig = localStorage.removeItem;
    localStorage.removeItem = () => { throw new Error('fail'); };

    try {
      expect(() => tokenStorage.removeToken()).not.toThrow();
    } finally {
      localStorage.removeItem = orig;
    }
  });
});

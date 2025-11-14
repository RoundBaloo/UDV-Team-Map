const TOKEN_KEY = 'udv_access_token';

export const tokenStorage = {
  // Получить токен
  getToken: () => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch (error) {
      console.error('Error getting token from storage:', error);
      return null;
    }
  },

  // Сохранить токен
  setToken: (token) => {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch (error) {
      console.error('Error saving token to storage:', error);
    }
  },

  // Удалить токен
  removeToken: () => {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch (error) {
      console.error('Error removing token from storage:', error);
    }
  },

  // Проверить наличие токена
  hasToken: () => {
    return !!tokenStorage.getToken();
  },
};
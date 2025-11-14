import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

export const authApi = {
  // Логин
  login: async (email, password) => {
    const data = await apiClient.post(API_ENDPOINTS.AUTH.LOGIN, {
      email,
      password,
    });
    return data;
  },

  // Получить текущего пользователя
  getMe: async () => {
    const data = await apiClient.get(API_ENDPOINTS.AUTH.ME);
    return data;
  },

  // Выход (на клиенте просто удаляем токен)
  logout: () => {
    return Promise.resolve();
  },
};
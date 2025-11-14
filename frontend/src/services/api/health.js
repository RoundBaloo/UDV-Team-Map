import { apiClient } from './apiClient';

export const healthApi = {
  // Проверка доступности API
  checkHealth: async () => {
    try {
      const response = await apiClient.get('/health');
      return { 
        success: true, 
        data: response,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return { 
        success: false, 
        error: error.message,
        timestamp: new Date().toISOString(),
      };
    }
  },

  // Проверка аутентификации
  checkAuth: async () => {
    try {
      const response = await apiClient.get('/api/v1/auth/me');
      return { 
        success: true, 
        data: response,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return { 
        success: false, 
        error: error.message,
        timestamp: new Date().toISOString(),
      };
    }
  },
};
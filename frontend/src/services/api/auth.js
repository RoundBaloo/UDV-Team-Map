import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

export const authApi = {
  login: async (email, password) => {
    const response = await apiClient.post(API_ENDPOINTS.AUTH.LOGIN, {
      email,
      password,
    });
    
    return response;
  },

  getMe: async () => {
    const response = await apiClient.get(API_ENDPOINTS.AUTH.ME);
    return response;
  },

  logout: () => Promise.resolve(),
};
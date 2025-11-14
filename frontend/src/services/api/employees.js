import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

export const employeesApi = {
  // Получить список сотрудников
  getEmployees: async (params = {}) => {
    const queryParams = new URLSearchParams(params).toString();
    const endpoint = queryParams 
      ? `${API_ENDPOINTS.EMPLOYEES.LIST}?${queryParams}`
      : API_ENDPOINTS.EMPLOYEES.LIST;
    
    const data = await apiClient.get(endpoint);
    return data;
  },

  // Получить сотрудника по ID
  getEmployee: async (employeeId) => {
    const endpoint = API_ENDPOINTS.EMPLOYEES.DETAIL.replace('{employee_id}', employeeId.toString());
    const data = await apiClient.get(endpoint);
    return data;
  },

  // Получить текущего пользователя
  getCurrentEmployee: async () => {
    const data = await apiClient.get(API_ENDPOINTS.EMPLOYEES.ME);
    return data;
  },

  // Обновить данные текущего пользователя
  updateMe: async (employeeData) => {
    const data = await apiClient.patch(API_ENDPOINTS.EMPLOYEES.ME, employeeData);
    return data;
  },

  // Обновить данные сотрудника (админ)
  updateEmployee: async (employeeId, employeeData) => {
    const endpoint = API_ENDPOINTS.EMPLOYEES.DETAIL.replace('{employee_id}', employeeId.toString());
    const data = await apiClient.patch(endpoint, employeeData);
    return data;
  },
};
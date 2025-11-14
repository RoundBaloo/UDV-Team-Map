import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

export const orgUnitsApi = {
  // Получить всю организационную структуру
  getOrgStructure: async () => {
    try {
      const data = await apiClient.get(API_ENDPOINTS.ORG_UNITS.LIST);
      return data;
    } catch (error) {
      console.error('Error fetching org structure:', error);
      throw error;
    }
  },

  // Получить сотрудников конкретного подразделения
  getUnitEmployees: async (orgUnitId) => {
    try {
      const endpoint = API_ENDPOINTS.ORG_UNITS.UNIT_EMPLOYEES.replace('{org_unit_id}', orgUnitId.toString());
      const data = await apiClient.get(endpoint);
      return data;
    } catch (error) {
      console.error('Error fetching unit employees:', error);
      throw error;
    }
  },
};
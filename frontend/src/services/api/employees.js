import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';
import { buildEndpoint, buildQueryString } from '../../utils/apiHelpers';

const EMPLOYEES_ENDPOINTS = API_ENDPOINTS.EMPLOYEES;

export const employeesApi = {
  getEmployees: async (params = {}) => {
    const queryString = buildQueryString(params);
    const endpoint = `${EMPLOYEES_ENDPOINTS.LIST}${queryString}`;
    
    const response = await apiClient.get(endpoint);
    return response;
  },

  getEmployee: async employeeId => {
    const endpoint = buildEndpoint(EMPLOYEES_ENDPOINTS.DETAIL, {
      employee_id: employeeId,
    });
    
    const response = await apiClient.get(endpoint);
    return response;
  },

  getCurrentEmployee: async () => {
    const response = await apiClient.get(EMPLOYEES_ENDPOINTS.ME);
    return response;
  },

  updateMe: async employeeData => {
    const response = await apiClient.patch(EMPLOYEES_ENDPOINTS.ME, employeeData);
    return response;
  },

  updateEmployee: async (employeeId, employeeData) => {
    const endpoint = buildEndpoint(EMPLOYEES_ENDPOINTS.DETAIL, {
      employee_id: employeeId,
    });
    
    const response = await apiClient.patch(endpoint, employeeData);
    return response;
  },

  searchSkills: async (params = {}) => {
    const queryString = buildQueryString(params);
    const endpoint = `/api/employees/skills/search${queryString}`;
    
    const response = await apiClient.get(endpoint);
    return response;
  },

  searchTitles: async (params = {}) => {
    const queryString = buildQueryString(params);
    const endpoint = `/api/employees/titles/search${queryString}`;
    
    const response = await apiClient.get(endpoint);
    return response;
  },
};
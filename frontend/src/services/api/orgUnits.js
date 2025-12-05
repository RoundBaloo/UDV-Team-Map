import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';
import { buildEndpoint, buildQueryString } from '../../utils/apiHelpers';

const ORG_UNITS_ENDPOINTS = API_ENDPOINTS.ORG_UNITS;

export const orgUnitsApi = {
  getOrgStructure: async () => {
    const response = await apiClient.get(ORG_UNITS_ENDPOINTS.LIST);
    return response;
  },

  searchOrgUnits: async (params = {}) => {
    const queryString = buildQueryString(params);
    const endpoint = `/api/org-units/search${queryString}`;
    
    const response = await apiClient.get(endpoint);
    return response;
  },

  getDomains: async () => {
    const response = await apiClient.get('/api/org-units/domains');
    return response;
  },

  searchLegalEntities: async (params = {}) => {
    const queryString = buildQueryString(params);
    const endpoint = `/api/org-units/legal-entities/search${queryString}`;
    
    const response = await apiClient.get(endpoint);
    return response;
  },

  getUnitEmployees: async (orgUnitId, params = {}) => {
    const queryString = buildQueryString(params);
    const endpoint = buildEndpoint(ORG_UNITS_ENDPOINTS.UNIT_EMPLOYEES, {
      org_unit_id: orgUnitId,
    }) + queryString;
    
    const response = await apiClient.get(endpoint);
    return response;
  },
};
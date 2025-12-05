import { apiClient } from './apiClient';
import { buildQueryString } from '../../utils/apiHelpers';

export const syncApi = {
  getJobs: async (params = {}) => {
    const queryString = buildQueryString(params);
    const endpoint = `/api/sync/jobs${queryString}`;
    
    const response = await apiClient.get(endpoint);
    return response;
  },

  getJobDetail: async (jobId, params = {}) => {
    const queryString = buildQueryString(params);
    const endpoint = `/api/sync/jobs/${jobId}${queryString}`;
    
    const response = await apiClient.get(endpoint);
    return response;
  },

  runSync: async () => {
    const response = await apiClient.post('/api/sync/jobs/run');
    return response;
  },
};
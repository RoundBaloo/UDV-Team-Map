import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

const MODERATION_ENDPOINTS = API_ENDPOINTS.PHOTO_MODERATION;

export const photoModerationApi = {
  getPendingPhotos: async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = queryString 
      ? `${MODERATION_ENDPOINTS.PENDING}?${queryString}`
      : MODERATION_ENDPOINTS.PENDING;
    
    const response = await apiClient.get(endpoint);
    return response;
  },

  approvePhoto: async moderationId => {
    const endpoint = MODERATION_ENDPOINTS.DECISION.replace(
      '{moderation_id}', 
      moderationId.toString(),
    );
    
    const response = await apiClient.post(endpoint, {
      decision: 'approve',
      reason: null,
    });
    
    return response;
  },

  rejectPhoto: async (moderationId, reason) => {
    const endpoint = MODERATION_ENDPOINTS.DECISION.replace(
      '{moderation_id}', 
      moderationId.toString(),
    );
    
    const response = await apiClient.post(endpoint, {
      decision: 'reject',
      reason,
    });
    
    return response;
  },

  getMyModerationStatus: async () => {
    const response = await apiClient.get(MODERATION_ENDPOINTS.MY_STATUS);
    return response;
  },

  createModerationRequest: async mediaId => {
    const response = await apiClient.post(MODERATION_ENDPOINTS.REQUESTS_ME, {
      media_id: mediaId,
    });
    
    return response;
  },
};
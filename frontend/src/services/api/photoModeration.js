import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

export const photoModerationApi = {
  // Получить список фото на модерацию
  getPendingPhotos: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams(params).toString();
      const endpoint = queryParams 
        ? `${API_ENDPOINTS.PHOTO_MODERATION.PENDING}?${queryParams}`
        : API_ENDPOINTS.PHOTO_MODERATION.PENDING;
      
      const data = await apiClient.get(endpoint);
      return data;
    } catch (error) {
      console.error('Error fetching pending photos:', error);
      throw error;
    }
  },

  // ОДОБРИТЬ фото (использует новый decision эндпоинт)
  approvePhoto: async (moderationId) => {
    try {
      const endpoint = API_ENDPOINTS.PHOTO_MODERATION.DECISION.replace('{moderation_id}', moderationId.toString());
      const data = await apiClient.post(endpoint, { 
        decision: 'approve',
        reason: null,
      });
      return data;
    } catch (error) {
      console.error('Error approving photo:', error);
      throw error;
    }
  },

  // ОТКЛОНИТЬ фото (использует новый decision эндпоинт)
  rejectPhoto: async (moderationId, reason) => {
    try {
      const endpoint = API_ENDPOINTS.PHOTO_MODERATION.DECISION.replace('{moderation_id}', moderationId.toString());
      const data = await apiClient.post(endpoint, { 
        decision: 'reject',
        reason: reason,
      });
      return data;
    } catch (error) {
      console.error('Error rejecting photo:', error);
      throw error;
    }
  },

  // Получить статус модерации текущего пользователя
  getMyModerationStatus: async () => {
    try {
      const data = await apiClient.get(API_ENDPOINTS.PHOTO_MODERATION.MY_STATUS);
      return data;
    } catch (error) {
      console.error('Error fetching moderation status:', error);
      throw error;
    }
  },

  // Создать запрос на модерацию (для пользователя)
  createModerationRequest: async (mediaId) => {
    try {
      const data = await apiClient.post(API_ENDPOINTS.PHOTO_MODERATION.REQUESTS_ME, { 
        media_id: mediaId,
      });
      return data;
    } catch (error) {
      console.error('Error creating moderation request:', error);
      throw error;
    }
  },
};
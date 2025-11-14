// src/services/api/media.js - ЗАМЕНИ весь файл на это:

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

export const mediaApi = {
  // Инициализация загрузки
  initUpload: async (contentType) => {
    try {
      const data = await apiClient.post(API_ENDPOINTS.MEDIA.INIT_UPLOAD, {
        content_type: contentType,
      });
      return data;
    } catch (error) {
      console.error('Error initializing upload:', error);
      throw error;
    }
  },

  // Загрузка файла на presigned URL с прогрессом
  uploadToPresignedUrl: (uploadUrl, file, onProgress) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.open('PUT', uploadUrl);
      xhr.setRequestHeader('Content-Type', file.type);

      // Отслеживаем прогресс
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && onProgress) {
          const percentComplete = (event.loaded / event.total) * 100;
          onProgress(Math.round(percentComplete));
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      };

      xhr.onerror = () => reject(new Error('Network error during upload'));
      xhr.onabort = () => reject(new Error('Upload aborted'));

      xhr.send(file);
    });
  },

  // Финаллизация загрузки
  finalizeUpload: async (storageKey) => {
    try {
      const data = await apiClient.post(API_ENDPOINTS.MEDIA.FINALIZE_UPLOAD, {
        storage_key: storageKey,
      });
      return data;
    } catch (error) {
      console.error('Error finalizing upload:', error);
      throw error;
    }
  },
};
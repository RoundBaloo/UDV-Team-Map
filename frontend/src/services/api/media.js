import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

const MEDIA_ENDPOINTS = API_ENDPOINTS.MEDIA;

export const mediaApi = {
  initUpload: async contentType => {
    const response = await apiClient.post(MEDIA_ENDPOINTS.INIT_UPLOAD, {
      content_type: contentType,
    });
    
    return response;
  },

  uploadToPresignedUrl: (uploadUrl, file, onProgress) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.open('PUT', uploadUrl);
      xhr.setRequestHeader('Content-Type', file.type);

      xhr.upload.onprogress = event => {
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

  finalizeUpload: async storageKey => {
    const response = await apiClient.post(MEDIA_ENDPOINTS.FINALIZE_UPLOAD, {
      storage_key: storageKey,
    });
    
    return response;
  },
};
import { mediaApi } from '../services/api/media';
import { photoModerationApi } from '../services/api/photoModeration';

export const uploadAvatarWithModeration = async (file, onProgress) => {
  if (!file) throw new Error('No file selected');
  
  if (!file.type.startsWith('image/')) {
    throw new Error('Пожалуйста, выберите изображение');
  }

  if (file.size > 5 * 1024 * 1024) {
    throw new Error('Размер файла не должен превышать 5MB');
  }

  try {
    // 1. Инициализация загрузки
    const initResponse = await mediaApi.initUpload(file.type);
    console.log('Init storage_key:', initResponse.storage_key);

    // 2. Загрузка на presigned URL
    await mediaApi.uploadToPresignedUrl(
      initResponse.upload_url,
      file,
      onProgress
    );

    // 3. Финаллизация загрузки
    const mediaItem = await mediaApi.finalizeUpload(initResponse.storage_key);
    console.log('Finalize public_url:', mediaItem.public_url);
    console.log('Finalize storage_key:', mediaItem.storage_key);
    console.log('Finalize media_id:', mediaItem.media_id); 

    // 4. Создание запроса на модерацию
    const moderationItem = await photoModerationApi.createModerationRequest(
      mediaItem.media_id || mediaItem.id 
    );

    return {
      media: mediaItem,
      moderation: moderationItem,
      publicUrl: mediaItem.public_url,
    };

  } catch (error) {
    console.error('Upload error:', error);
    throw error;
  }
};
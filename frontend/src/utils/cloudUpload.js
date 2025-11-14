// src/utils/uploadHelpers.js
import { mediaApi } from '../services/api/media';
import { photoModerationApi } from '../services/api/photoModeration';

export const uploadAvatarWithModeration = async (file, onProgress) => {
  if (!file) throw new Error('No file selected');
  
  // Валидация файла
  if (!file.type.startsWith('image/')) {
    throw new Error('Пожалуйста, выберите изображение');
  }

  // Проверка размера (5MB)
  if (file.size > 5 * 1024 * 1024) {
    throw new Error('Размер файла не должен превышать 5MB');
  }

  try {
    console.log('1. Инициализация загрузки...');
    
    // 1. Инициализация загрузки
    const initResponse = await mediaApi.initUpload(file.type);
    console.log('Init response:', initResponse);

    // 2. Загрузка на presigned URL с прогрессом
    console.log('2. Загрузка файла на presigned URL...');
    await mediaApi.uploadToPresignedUrl(
      initResponse.upload_url,
      file,
      (progress) => {
        // Прогресс от 0 до 100%
        onProgress?.(progress);
      }
    );

    // 3. Финаллизация загрузки
    console.log('3. Финаллизация загрузки...');
    const mediaItem = await mediaApi.finalizeUpload(initResponse.storage_key);
    console.log('Media item:', mediaItem);

    // 4. Создание запроса на модерацию
    console.log('4. Создание запроса на модерацию...');
    const moderationItem = await photoModerationApi.createModerationRequest(mediaItem.id);
    console.log('Moderation item:', moderationItem);

    return {
      media: mediaItem,
      moderation: moderationItem,
      publicUrl: mediaItem.public_url, // Для немедленного превью
    };

  } catch (error) {
    console.error('Error in upload process:', error);
    throw error;
  }
};

// Функция для конвертации HEIC в JPEG (если понадобится)
export const convertHeicToJpeg = async (file) => {
  // Для реализации нужно добавить библиотеку heic2any
  // Пока просто возвращаем оригинальный файл
  return file;
};
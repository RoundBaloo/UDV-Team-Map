// src/utils/cloudUpload.test.js
import { uploadAvatarWithModeration, convertHeicToJpeg } from './cloudUpload';
import { mediaApi } from '../services/api/media';
import { photoModerationApi } from '../services/api/photoModeration';

jest.mock('../services/api/media', () => ({
  mediaApi: {
    initUpload: jest.fn(),
    uploadToPresignedUrl: jest.fn(),
    finalizeUpload: jest.fn(),
  },
}));

jest.mock('../services/api/photoModeration', () => ({
  photoModerationApi: {
    createModerationRequest: jest.fn(),
  },
}));

describe('cloudUpload', () => {
  const mockFile = new File(['dummy'], 'avatar.png', { type: 'image/png', size: 1024 });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('выбрасывает ошибку если файл не передан', async () => {
    await expect(uploadAvatarWithModeration(null)).rejects.toThrow('No file selected');
  });

  test('выбрасывает ошибку если тип файла не image/*', async () => {
    const file = new File(['text'], 'file.txt', { type: 'text/plain', size: 1024 });
    await expect(uploadAvatarWithModeration(file)).rejects.toThrow('Пожалуйста, выберите изображение');
  });

  test('выбрасывает ошибку если размер файла больше 5MB', async () => {
    const file = new File(['a'.repeat(6 * 1024 * 1024)], 'big.png', { type: 'image/png', size: 6 * 1024 * 1024 });
    await expect(uploadAvatarWithModeration(file)).rejects.toThrow('Размер файла не должен превышать 5MB');
  });

  test('успешная загрузка вызывает все методы и возвращает объект', async () => {
    const initResp = { upload_url: 'url', storage_key: 'key123' };
    const mediaItem = { id: 'media1', public_url: 'https://example.com/avatar.png' };
    const moderationItem = { id: 'mod1' };

    mediaApi.initUpload.mockResolvedValue(initResp);
    mediaApi.uploadToPresignedUrl.mockResolvedValue();
    mediaApi.finalizeUpload.mockResolvedValue(mediaItem);
    photoModerationApi.createModerationRequest.mockResolvedValue(moderationItem);

    const progress = jest.fn();

    const result = await uploadAvatarWithModeration(mockFile, progress);

    expect(mediaApi.initUpload).toHaveBeenCalledWith('image/png');
    expect(mediaApi.uploadToPresignedUrl).toHaveBeenCalledWith(initResp.upload_url, mockFile, expect.any(Function));
    expect(mediaApi.finalizeUpload).toHaveBeenCalledWith(initResp.storage_key);
    expect(photoModerationApi.createModerationRequest).toHaveBeenCalledWith(mediaItem.id);
    expect(result).toEqual({
      media: mediaItem,
      moderation: moderationItem,
      publicUrl: mediaItem.public_url,
    });
  });

  test('ловит ошибки в процессе загрузки и пробрасывает их', async () => {
    const error = new Error('Upload failed');
    mediaApi.initUpload.mockRejectedValue(error);
    await expect(uploadAvatarWithModeration(mockFile)).rejects.toThrow(error);
  });

  test('convertHeicToJpeg возвращает исходный файл', async () => {
    const file = new File(['heic'], 'file.heic', { type: 'image/heic', size: 100 });
    const result = await convertHeicToJpeg(file);
    expect(result).toBe(file);
  });
});

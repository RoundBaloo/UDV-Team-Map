// src/utils/uploadHelpers.test.js
import { uploadAvatarWithModeration } from './uploadHelpers';
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

describe('uploadHelpers', () => {
  const mockFile = new File(['dummy content'], 'avatar.png', { type: 'image/png', size: 1024 });

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

  test('выбрасывает ошибку если размер файла > 5MB', async () => {
    const file = new File(['a'.repeat(6 * 1024 * 1024)], 'big.png', { type: 'image/png', size: 6 * 1024 * 1024 });
    await expect(uploadAvatarWithModeration(file)).rejects.toThrow('Размер файла не должен превышать 5MB');
  });

  test('успешная загрузка вызывает все методы и возвращает объект', async () => {
    const initResponse = { upload_url: 'url', storage_key: 'key123' };
    const mediaItem = { id: 'media1', media_id: 'media1', storage_key: 'key123', public_url: 'https://example.com/avatar.png' };
    const moderationItem = { id: 'mod1' };

    mediaApi.initUpload.mockResolvedValue(initResponse);
    mediaApi.uploadToPresignedUrl.mockResolvedValue();
    mediaApi.finalizeUpload.mockResolvedValue(mediaItem);
    photoModerationApi.createModerationRequest.mockResolvedValue(moderationItem);

    const progressFn = jest.fn();

    const result = await uploadAvatarWithModeration(mockFile, progressFn);

    expect(mediaApi.initUpload).toHaveBeenCalledWith('image/png');
    expect(mediaApi.uploadToPresignedUrl).toHaveBeenCalledWith(initResponse.upload_url, mockFile, progressFn);
    expect(mediaApi.finalizeUpload).toHaveBeenCalledWith(initResponse.storage_key);
    expect(photoModerationApi.createModerationRequest).toHaveBeenCalledWith(mediaItem.media_id);
    expect(result).toEqual({
      media: mediaItem,
      moderation: moderationItem,
      publicUrl: mediaItem.public_url,
    });
  });

  test('ловит ошибки и выбрасывает их', async () => {
    const error = new Error('Upload failed');
    mediaApi.initUpload.mockRejectedValue(error);
    await expect(uploadAvatarWithModeration(mockFile)).rejects.toThrow(error);
  });
});

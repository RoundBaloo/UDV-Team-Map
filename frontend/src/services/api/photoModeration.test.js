import { photoModerationApi } from './photoModeration';
import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

jest.mock('./apiClient');

describe('photoModerationApi', () => {
  beforeEach(() => jest.clearAllMocks());

  test('getPendingPhotos без params вызывает apiClient.get с PENDING', async () => {
    apiClient.get.mockResolvedValue([{ id: 1 }]);
    const res = await photoModerationApi.getPendingPhotos();
    expect(apiClient.get).toHaveBeenCalledWith(API_ENDPOINTS.PHOTO_MODERATION.PENDING);
    expect(res).toEqual([{ id: 1 }]);
  });

  test('getPendingPhotos с params добавляет query string', async () => {
    apiClient.get.mockResolvedValue([{ id: 2 }]);
    const res = await photoModerationApi.getPendingPhotos({ page: 1 });
    expect(apiClient.get).toHaveBeenCalledWith(`${API_ENDPOINTS.PHOTO_MODERATION.PENDING}?page=1`);
    expect(res).toEqual([{ id: 2 }]);
  });

  test('approvePhoto вызывает POST с decision approve', async () => {
    apiClient.post.mockResolvedValue({ success: true });
    const moderationId = 123;
    const res = await photoModerationApi.approvePhoto(moderationId);
    const endpoint = API_ENDPOINTS.PHOTO_MODERATION.DECISION.replace('{moderation_id}', moderationId.toString());
    expect(apiClient.post).toHaveBeenCalledWith(endpoint, { decision: 'approve', reason: null });
    expect(res).toEqual({ success: true });
  });

  test('rejectPhoto вызывает POST с decision reject и reason', async () => {
    apiClient.post.mockResolvedValue({ success: true });
    const moderationId = 456;
    const reason = 'bad photo';
    const res = await photoModerationApi.rejectPhoto(moderationId, reason);
    const endpoint = API_ENDPOINTS.PHOTO_MODERATION.DECISION.replace('{moderation_id}', moderationId.toString());
    expect(apiClient.post).toHaveBeenCalledWith(endpoint, { decision: 'reject', reason });
    expect(res).toEqual({ success: true });
  });

  test('getMyModerationStatus вызывает apiClient.get с MY_STATUS', async () => {
    apiClient.get.mockResolvedValue({ status: 'pending' });
    const res = await photoModerationApi.getMyModerationStatus();
    expect(apiClient.get).toHaveBeenCalledWith(API_ENDPOINTS.PHOTO_MODERATION.MY_STATUS);
    expect(res).toEqual({ status: 'pending' });
  });

  test('createModerationRequest вызывает POST с media_id', async () => {
    apiClient.post.mockResolvedValue({ success: true });
    const mediaId = 789;
    const res = await photoModerationApi.createModerationRequest(mediaId);
    expect(apiClient.post).toHaveBeenCalledWith(API_ENDPOINTS.PHOTO_MODERATION.REQUESTS_ME, { media_id: mediaId });
    expect(res).toEqual({ success: true });
  });
});

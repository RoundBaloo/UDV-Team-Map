import { syncApi } from './sync';
import { apiClient } from './apiClient';

jest.mock('./apiClient');

describe('syncApi', () => {
  beforeEach(() => jest.clearAllMocks());

  test('getJobs без params вызывает apiClient.get с правильным endpoint', async () => {
    apiClient.get.mockResolvedValue([{ id: 1 }]);
    const res = await syncApi.getJobs();
    expect(apiClient.get).toHaveBeenCalledWith('/api/sync/jobs');
    expect(res).toEqual([{ id: 1 }]);
  });

  test('getJobs с params добавляет query string', async () => {
    apiClient.get.mockResolvedValue([{ id: 2 }]);
    const res = await syncApi.getJobs({ page: 1 });
    expect(apiClient.get).toHaveBeenCalledWith('/api/sync/jobs?page=1');
    expect(res).toEqual([{ id: 2 }]);
  });

  test('getJobDetail вызывает apiClient.get с jobId и params', async () => {
    apiClient.get.mockResolvedValue({ id: 3 });
    const res = await syncApi.getJobDetail(42, { verbose: true });
    expect(apiClient.get).toHaveBeenCalledWith('/api/sync/jobs/42?verbose=true');
    expect(res).toEqual({ id: 3 });
  });

  test('runSync вызывает POST на /api/sync/jobs/run', async () => {
    apiClient.post.mockResolvedValue({ success: true });
    const res = await syncApi.runSync();
    expect(apiClient.post).toHaveBeenCalledWith('/api/sync/jobs/run');
    expect(res).toEqual({ success: true });
  });
});

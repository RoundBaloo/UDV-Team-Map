import { healthApi } from './health';
import { apiClient } from './apiClient';

describe('healthApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('checkHealth возвращает success и данные при успешном get', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue({ status: 'ok' });

    const res = await healthApi.checkHealth();
    expect(res.success).toBe(true);
    expect(res.data).toEqual({ status: 'ok' });
    expect(typeof res.timestamp).toBe('string');
  });

  test('checkHealth возвращает ошибку при падении apiClient.get', async () => {
    jest.spyOn(apiClient, 'get').mockRejectedValue(new Error('Network error'));

    const res = await healthApi.checkHealth();
    expect(res.success).toBe(false);
    expect(res.error).toBe('Network error');
    expect(typeof res.timestamp).toBe('string');
  });

  test('checkAuth возвращает success и данные при успешном get', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue({ id: 1 });
    const res = await healthApi.checkAuth();
    expect(res.success).toBe(true);
    expect(res.data).toEqual({ id: 1 });
  });
});

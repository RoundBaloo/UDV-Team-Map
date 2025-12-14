import { authApi } from './auth';
import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

describe('authApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('login вызывает apiClient.post с правильными данными', async () => {
    jest.spyOn(apiClient, 'post').mockResolvedValue({ access_token: 'abc' });

    const res = await authApi.login('test@test.com', 'pass');
    expect(apiClient.post).toHaveBeenCalledWith(API_ENDPOINTS.AUTH.LOGIN, {
      email: 'test@test.com',
      password: 'pass',
    });
    expect(res).toEqual({ access_token: 'abc' });
  });
  
  test('getMe вызывает apiClient.get', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue({ employee_id: 1 });
    const res = await authApi.getMe();
    expect(apiClient.get).toHaveBeenCalledWith(API_ENDPOINTS.AUTH.ME);
    expect(res).toEqual({ employee_id: 1 });
  });

  test('logout резолвится (пустая реализация)', async () => {
    await expect(authApi.logout()).resolves.toBeUndefined();
  });
});

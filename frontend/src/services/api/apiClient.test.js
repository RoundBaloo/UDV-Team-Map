import '@testing-library/jest-dom';
import { apiClient } from './apiClient';
import { tokenStorage } from '../storage/tokenStorage';
import { API_CONFIG } from '../../utils/constants';

describe('apiClient', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
    jest.spyOn(tokenStorage, 'getToken').mockReturnValue('mock-token');
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('добавляет Authorization заголовок, если токен существует', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: 'ok' }),
    });

    const result = await apiClient.get('/test');

    expect(fetch).toHaveBeenCalledTimes(1);
    const callArgs = fetch.mock.calls[0];
    const config = callArgs[1];

    if (config.headers instanceof Headers) {
      expect(config.headers.get('Authorization')).toBe('Bearer mock-token');
    } else {
      expect(config.headers.Authorization).toBe('Bearer mock-token');
    }

    expect(result).toEqual({ data: 'ok' });
  });

  test('выбрасывает ошибку с сообщением из detail для не-ok response', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Bad request' }),
    });

    await expect(apiClient.get('/error')).rejects.toThrow('Bad request');
  });

  test('возвращает null для EMPTY_RESPONSE_STATUS', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: API_CONFIG.EMPTY_RESPONSE_STATUS,
      json: async () => ({}),
    });

    const res = await apiClient.get('/empty');
    expect(res).toBeNull();
  });

  test('если response.json падает, выбрасывает ошибку', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => { throw new Error('parse error'); },
    });

    await expect(apiClient.get('/err')).rejects.toThrow('parse error');
  });
});

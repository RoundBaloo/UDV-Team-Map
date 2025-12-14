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

  test('если response.json падает, использует HTTP ошибку', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => { throw new Error('parse error'); },
    });

    await expect(apiClient.get('/err')).rejects.toThrow('Ошибка сервера');
  });

  test('если response.json падает с не-Error, использует HTTP ошибку', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => { throw 'string error'; }, // не Error объект
    });

    await expect(apiClient.get('/err')).rejects.toThrow('Ошибка сервера');
  });

  test('extractErrorMessage возвращает DEFAULT, если detail отсутствует', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ message: 'Some error' }), // нет detail
    });

    await expect(apiClient.get('/error')).rejects.toThrow('Произошла ошибка');
  });

  test('extractErrorMessage обрабатывает массив detail', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ 
        detail: [
          { msg: 'Error 1' },
          { msg: 'Error 2' },
        ]
      }),
    });

    await expect(apiClient.get('/error')).rejects.toThrow('Error 1, Error 2');
  });

  test('getHttpErrorMessage возвращает правильное сообщение для известных статусов', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => { throw 'parse error'; },
    });

    await expect(apiClient.get('/err')).rejects.toThrow('Неавторизованный доступ');
  });

  test('getHttpErrorMessage возвращает DEFAULT для неизвестных статусов', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 418, // неизвестный статус
      json: async () => { throw 'parse error'; },
    });

    await expect(apiClient.get('/err')).rejects.toThrow('Произошла ошибка');
  });

  test('post вызывает request с правильными параметрами', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ success: true }),
    });

    const result = await apiClient.post('/test', { name: 'Test' });

    expect(fetch).toHaveBeenCalledTimes(1);
    const callArgs = fetch.mock.calls[0];
    const config = callArgs[1];
    
    expect(config.method).toBe('POST');
    expect(config.body).toBe(JSON.stringify({ name: 'Test' }));
    expect(result).toEqual({ success: true });
  });

  test('patch вызывает request с правильными параметрами', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ updated: true }),
    });

    const result = await apiClient.patch('/test/1', { name: 'Updated' });

    expect(fetch).toHaveBeenCalledTimes(1);
    const callArgs = fetch.mock.calls[0];
    const config = callArgs[1];
    
    expect(config.method).toBe('PATCH');
    expect(config.body).toBe(JSON.stringify({ name: 'Updated' }));
    expect(result).toEqual({ updated: true });
  });

  test('delete вызывает request с правильными параметрами', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ deleted: true }),
    });

    const result = await apiClient.delete('/test/1');

    expect(fetch).toHaveBeenCalledTimes(1);
    const callArgs = fetch.mock.calls[0];
    const config = callArgs[1];
    
    expect(config.method).toBe('DELETE');
    expect(result).toEqual({ deleted: true });
  });

  test('post обрабатывает ошибки', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Validation error' }),
    });

    await expect(apiClient.post('/test', {})).rejects.toThrow('Validation error');
  });

  test('patch обрабатывает ошибки', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' }),
    });

    await expect(apiClient.patch('/test/1', {})).rejects.toThrow('Not found');
  });

  test('delete обрабатывает ошибки', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Forbidden' }),
    });

    await expect(apiClient.delete('/test/1')).rejects.toThrow('Forbidden');
  });
});

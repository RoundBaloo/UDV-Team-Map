// apiHelpers.test.js
import { buildEndpoint, buildQueryString } from './apiHelpers';

describe('buildEndpoint', () => {
  test('заменяет path параметры', () => {
    const result = buildEndpoint('/users/{id}/posts/{postId}', { id: 5, postId: 10 });
    expect(result).toBe('/users/5/posts/10');
  });

  test('оставляет endpoint без изменений если нет совпадений', () => {
    const result = buildEndpoint('/users/list', { id: 5 });
    expect(result).toBe('/users/list');
  });

  test('частично заменяет только совпавшие ключи', () => {
    const result = buildEndpoint('/users/{id}/posts/{postId}', { id: 5 });
    expect(result).toBe('/users/5/posts/{postId}');
  });

  test('конвертирует значения параметров в строку', () => {
    const result = buildEndpoint('/items/{id}', { id: 123 });
    expect(result).toBe('/items/123');
  });
});

describe('buildQueryString', () => {
  test('создает query строку из нескольких параметров', () => {
    const result = buildQueryString({ page: 2, limit: 10 });
    expect(result).toBe('?page=2&limit=10');
  });

  test('игнорирует null и undefined значения', () => {
    const result = buildQueryString({ page: 2, limit: null, search: undefined });
    expect(result).toBe('?page=2');
  });

  test('возвращает пустую строку если нет параметров', () => {
    const result = buildQueryString();
    expect(result).toBe('');
  });

  test('конвертирует значения параметров в строки', () => {
    const result = buildQueryString({ active: true, count: 5 });
    expect(result).toBe('?active=true&count=5');
  });
});

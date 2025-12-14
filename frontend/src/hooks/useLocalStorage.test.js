// src/hooks/useLocalStorage.test.js
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from './useLocalStorage';

describe('useLocalStorage hook', () => {
  const KEY = 'testKey';
  const INITIAL_VALUE = { foo: 'bar' };

  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  test('initializes with localStorage value if present', () => {
    localStorage.setItem(KEY, JSON.stringify({ foo: 'baz' }));

    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));
    expect(result.current[0]).toEqual({ foo: 'baz' });
  });

  test('initializes with initialValue if localStorage empty', () => {
    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));
    expect(result.current[0]).toEqual(INITIAL_VALUE);
  });

  test('setValue updates state and localStorage', () => {
    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));

    act(() => result.current[1]({ foo: 'updated' }));

    expect(result.current[0]).toEqual({ foo: 'updated' });
    expect(JSON.parse(localStorage.getItem(KEY))).toEqual({ foo: 'updated' });
  });

  test('setValue works with function updater', () => {
    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));

    act(() => result.current[1](prev => ({ ...prev, newKey: 123 })));

    expect(result.current[0]).toEqual({ foo: 'bar', newKey: 123 });
    expect(JSON.parse(localStorage.getItem(KEY))).toEqual({ foo: 'bar', newKey: 123 });
  });

  test('setValue removes item if value is undefined', () => {
    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));

    act(() => result.current[1](undefined));

    expect(result.current[0]).toBeUndefined();
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  test('removeValue clears state and localStorage', () => {
    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));

    act(() => result.current[2]());

    expect(result.current[0]).toBeUndefined();
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  test('handles localStorage getItem error gracefully', () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('fail get'); });
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));
    expect(result.current[0]).toEqual(INITIAL_VALUE);
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Error reading localStorage key'), expect.any(Error));

    consoleSpy.mockRestore();
  });

  test('handles localStorage setItem error gracefully', () => {
    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('fail set'); });
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));
    act(() => result.current[1]({ foo: 'x' }));

    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Error setting localStorage key'), expect.any(Error));

    consoleSpy.mockRestore();
  });

  test('handles localStorage removeItem error gracefully', () => {
    jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => { throw new Error('fail remove'); });
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));
    act(() => result.current[2]());

    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Error removing localStorage key'), expect.any(Error));

    consoleSpy.mockRestore();
  });

  test('updates state when storage event fires for same key', () => {
    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));

    act(() => {
      window.dispatchEvent(new StorageEvent('storage', {
        key: KEY,
        newValue: JSON.stringify({ foo: 'event' }),
        storageArea: localStorage,
      }));
    });

    expect(result.current[0]).toEqual({ foo: 'event' });
  });

  test('handles invalid JSON in storage event gracefully', () => {
    const { result } = renderHook(() => useLocalStorage(KEY, INITIAL_VALUE));
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    act(() => {
      window.dispatchEvent(new StorageEvent('storage', {
        key: KEY,
        newValue: '{ invalid json }',
        storageArea: localStorage,
      }));
    });

    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Error reading localStorage key'), expect.any(Error));
    expect(result.current[0]).toEqual(INITIAL_VALUE);

    consoleSpy.mockRestore();
  });
});

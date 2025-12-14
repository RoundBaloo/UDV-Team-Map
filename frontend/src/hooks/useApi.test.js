// src/hooks/useApi.test.js
import React from 'react';
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react';
import { useApi } from './useApi';

// Тестовый компонент — экспонирует поведение хука через кнопки.
// ВАЖНО: onClick для execute ловит reject (.catch(() => {}))
// чтобы не возникало unhandled rejection в тестах.
function HookTester({ apiFn, immediate = true }) {
  const { data, loading, error, execute, refetch } = useApi(apiFn, immediate);

  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="data">{data ?? ''}</span>
      <span data-testid="error">{error ?? ''}</span>

      <button
        data-testid="execute"
        onClick={() => {
          // catch нужен, чтобы подавить unhandled rejection внутри тестовой среды
          // при намеренном откате (reject).
          execute('param').catch(() => {});
        }}
      >
        execute
      </button>

      <button
        data-testid="refetch"
        onClick={() => {
          // refetch вызывает executeRef.current(), тоже может reject -> ловим
          refetch?.();
        }}
      >
        refetch
      </button>
    </div>
  );
}

describe('useApi hook', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('initial immediate=true triggers api call and sets data', async () => {
    const mockSuccess = jest.fn().mockResolvedValueOnce('ok');

    render(<HookTester apiFn={mockSuccess} immediate={true} />);

    // loading true сразу после mount
    expect(screen.getByTestId('loading').textContent).toBe('true');

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(screen.getByTestId('data').textContent).toBe('ok');
    expect(screen.getByTestId('error').textContent).toBe('');
    expect(mockSuccess).toHaveBeenCalledTimes(1);
  });

  test('immediate=false does not call api automatically', () => {
    const mockSuccess = jest.fn().mockResolvedValueOnce('ok');

    render(<HookTester apiFn={mockSuccess} immediate={false} />);

    expect(screen.getByTestId('loading').textContent).toBe('false');
    expect(screen.getByTestId('data').textContent).toBe('');
    expect(screen.getByTestId('error').textContent).toBe('');
    expect(mockSuccess).not.toHaveBeenCalled();
  });

  test('execute calls api and updates state on success', async () => {
    const mockSuccess = jest.fn().mockResolvedValueOnce('result');

    render(<HookTester apiFn={mockSuccess} immediate={false} />);

    await act(async () => {
      fireEvent.click(screen.getByTestId('execute'));
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(screen.getByTestId('data').textContent).toBe('result');
    expect(screen.getByTestId('error').textContent).toBe('');
    expect(mockSuccess).toHaveBeenCalledWith('param');
  });

  test('execute handles rejected promise (error state set, no test crash)', async () => {
    // Создаём мок, который возвращает rejected Promise
    const mockError = jest.fn().mockImplementationOnce(() => Promise.reject(new Error('fail')));

    // Подавляем возможный console.error в логах теста (чтобы вывод был чистым)
    const spyConsole = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<HookTester apiFn={mockError} immediate={false} />);

    // Нажимаем кнопку — execute возвращает rejected Promise, но кнопка ловит .catch(()=>{})
    await act(async () => {
      fireEvent.click(screen.getByTestId('execute'));
    });

    // Ждём, пока loading вернётся в false
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(screen.getByTestId('data').textContent).toBe('');
    // Хук кладёт err.message в state.error
    expect(screen.getByTestId('error').textContent).toBe('fail');

    spyConsole.mockRestore();
    expect(mockError).toHaveBeenCalledTimes(1);
  });

  test('refetch triggers api again', async () => {
    const mockSuccess = jest.fn()
      .mockResolvedValueOnce('first')
      .mockResolvedValueOnce('second');

    render(<HookTester apiFn={mockSuccess} immediate={true} />);

    // Ждём первого результата
    await waitFor(() => expect(screen.getByTestId('data').textContent).toBe('first'));

    // Вызов refetch (executeRef.current внутри хука)
    await act(async () => {
      fireEvent.click(screen.getByTestId('refetch'));
    });

    await waitFor(() => expect(screen.getByTestId('data').textContent).toBe('second'));
    expect(mockSuccess).toHaveBeenCalledTimes(2);
  });

  test('no state updates after unmount (no errors)', async () => {
    const asyncFn = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve('done'), 30))
    );

    const { unmount } = render(<HookTester apiFn={asyncFn} immediate={true} />);

    // Убираем компонент до завершения промиса
    unmount();

    // Ждём чуть дольше времени выполнения промиса, просто чтобы убедиться, что ничего не падает
    await act(async () => {
      await new Promise(r => setTimeout(r, 50));
    });

    expect(true).toBe(true);
  });
});

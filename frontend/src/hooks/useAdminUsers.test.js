// src/hooks/useAdminUsers.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { useAdminUsers } from './useAdminUsers';
import { apiClient } from '../services/api/apiClient';
import { API_ENDPOINTS } from '../utils/constants';

jest.mock('../services/api/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    patch: jest.fn(),
  },
}));

// Небольшой тестовый компонент для использования хука и отображения состояния в DOM
function HookTester() {
  const hook = useAdminUsers();

  return (
    <div>
      <span data-testid="loading">{String(hook.loading)}</span>
      <span data-testid="users-length">{hook.users.length}</span>
      <span data-testid="editing-id">{hook.editingId ?? ''}</span>
      <span data-testid="error">{hook.error ?? ''}</span>

      <button
        data-testid="btn-edit"
        onClick={() => hook.handleEdit(hook.users[0])}
      >
        edit
      </button>

      <button
        data-testid="btn-cancel"
        onClick={() => hook.handleCancel()}
      >
        cancel
      </button>

      <button
        data-testid="btn-field"
        onClick={() => hook.handleFieldChange('work_city', 'Санкт-Петербург')}
      >
        field
      </button>

      <button
        data-testid="btn-save"
        onClick={() => hook.handleSave(hook.users[0]?.id)}
      >
        save
      </button>

      <button
        data-testid="btn-refresh"
        onClick={() => hook.refreshUsers()}
      >
        refresh
      </button>

      {/* Показываем editedUser.work_city и полный users JSON для проверок */}
      <div data-testid="edited-work-city">{hook.editedUser?.work_city ?? ''}</div>
      <pre data-testid="users-json">{JSON.stringify(hook.users)}</pre>
    </div>
  );
}

describe('useAdminUsers hook (integration via HookTester)', () => {
  const mockApiUsers = [
    {
      employee_id: 1,
      email: 'ivanov@udv-group.ru',
      first_name: 'Иван',
      middle_name: 'Иванович',
      last_name: 'Иванов',
      title: 'Разработчик',
      status: 'active',
      work_city: 'Москва',
      work_format: 'office',
      time_zone: 'Europe/Moscow',
      work_phone: '+7 (999) 123-45-67',
      mattermost_handle: '@ivanov',
      telegram_handle: '@ivanov_telegram',
      birth_date: '1990-01-01',
      hire_date: '2020-01-15',
      bio: 'Опытный разработчик',
      skill_ratings: {},
      is_admin: false,
      is_blocked: false,
      last_login_at: '2024-01-15T10:30:00Z',
      photo: null,
      manager: null,
      org_unit: null,
    },
    {
      employee_id: 2,
      email: 'petrov@udv-group.ru',
      first_name: 'Петр',
      middle_name: '',
      last_name: 'Петров',
      title: 'Тимлид',
      status: 'active',
      work_city: null,
      work_format: null,
      time_zone: 'Europe/Moscow',
      work_phone: '+7 (999) 987-65-43',
      mattermost_handle: '@petrov',
      telegram_handle: '@petrov_telegram',
      birth_date: '1985-05-05',
      hire_date: '2018-03-10',
      bio: 'Тимлид команды',
      skill_ratings: {},
      is_admin: true,
      is_blocked: false,
      last_login_at: '2024-01-20T12:00:00Z',
      photo: null,
      manager: null,
      org_unit: null,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('инициализирует с загрузкой пользователей (успех)', async () => {
    apiClient.get.mockResolvedValueOnce(mockApiUsers);

    render(<HookTester />);

    // Сразу после монтирования — loading true
    expect(screen.getByTestId('loading').textContent).toBe('true');
    expect(screen.getByTestId('users-length').textContent).toBe('0');

    // Ждём, пока hook завершит загрузку
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(screen.getByTestId('users-length').textContent).toBe('2');

    // Проверяем, что имя собрано корректно (в users JSON)
    const usersJson = JSON.parse(screen.getByTestId('users-json').textContent);
    expect(usersJson[0].name).toBe('Иванов Иван Иванович');

    expect(apiClient.get).toHaveBeenCalledWith(API_ENDPOINTS.EMPLOYEES.LIST);
  });

  test('обрабатывает ошибку при загрузке', async () => {
    apiClient.get.mockRejectedValueOnce(new Error('API error'));

    render(<HookTester />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(screen.getByTestId('users-length').textContent).toBe('0');
    expect(screen.getByTestId('error').textContent).toBe('API error');
  });

  test('handleEdit устанавливает editingId и editedUser', async () => {
    apiClient.get.mockResolvedValueOnce(mockApiUsers);

    render(<HookTester />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    // Вызов handleEdit через кнопку
    act(() => {
      fireEvent.click(screen.getByTestId('btn-edit'));
    });

    // Ожидаем, что editingId и editedUser установлены
    expect(screen.getByTestId('editing-id').textContent).toBe('1');
    expect(screen.getByTestId('edited-work-city').textContent).toBe('Москва');
  });

  test('handleFieldChange обновляет editedUser', async () => {
    apiClient.get.mockResolvedValueOnce(mockApiUsers);

    render(<HookTester />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    act(() => {
      fireEvent.click(screen.getByTestId('btn-edit'));
    });

    act(() => {
      fireEvent.click(screen.getByTestId('btn-field'));
    });

    expect(screen.getByTestId('edited-work-city').textContent).toBe('Санкт-Петербург');
  });

  test('handleCancel сбрасывает редактирование', async () => {
    apiClient.get.mockResolvedValueOnce(mockApiUsers);

    render(<HookTester />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    act(() => {
      fireEvent.click(screen.getByTestId('btn-edit'));
    });

    // cancel
    act(() => {
      fireEvent.click(screen.getByTestId('btn-cancel'));
    });

    expect(screen.getByTestId('editing-id').textContent).toBe('');
    expect(screen.getByTestId('edited-work-city').textContent).toBe('');
  });

  test('handleSave обновляет пользователя и сбрасывает редактирование (успех)', async () => {
    apiClient.get.mockResolvedValueOnce(mockApiUsers);
    apiClient.patch.mockResolvedValueOnce({}); // успешный patch

    render(<HookTester />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    // edit + change field
    act(() => {
      fireEvent.click(screen.getByTestId('btn-edit'));
      fireEvent.click(screen.getByTestId('btn-field'));
    });

    // save (async)
    await act(async () => {
      fireEvent.click(screen.getByTestId('btn-save'));
    });

    // ждём, пока состояние обновится
    await waitFor(() => expect(screen.getByTestId('editing-id').textContent).toBe(''));

    // users JSON должен содержать обновление work_city
    const usersAfter = JSON.parse(screen.getByTestId('users-json').textContent);
    expect(usersAfter[0].work_city).toBe('Санкт-Петербург');

    expect(apiClient.patch).toHaveBeenCalledWith(
      API_ENDPOINTS.EMPLOYEES.DETAIL.replace('{employee_id}', 1),
      { work_city: 'Санкт-Петербург', work_format: 'office' }
    );
  });

  test('handleSave обрабатывает ошибку при патче (показывает alert и ставит error)', async () => {
    apiClient.get.mockResolvedValueOnce(mockApiUsers);
    apiClient.patch.mockRejectedValueOnce(new Error('Patch error'));

    // мок alert
    const alertSpy = jest.spyOn(global, 'alert').mockImplementation(() => {});

    render(<HookTester />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    act(() => {
      fireEvent.click(screen.getByTestId('btn-edit'));
      fireEvent.click(screen.getByTestId('btn-field'));
    });

    // save
    await act(async () => {
      fireEvent.click(screen.getByTestId('btn-save'));
    });

    await waitFor(() => expect(screen.getByTestId('error').textContent).toBe('Patch error'));
    expect(alertSpy).toHaveBeenCalledWith('Ошибка при сохранении изменений: Patch error');

    alertSpy.mockRestore();
  });

  test('refreshUsers вызывает загрузку повторно', async () => {
    apiClient.get.mockResolvedValueOnce(mockApiUsers);

    render(<HookTester />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    // подготовим ответ для второго вызова
    apiClient.get.mockResolvedValueOnce([]);

    act(() => {
      fireEvent.click(screen.getByTestId('btn-refresh'));
    });

    await waitFor(() => expect(screen.getByTestId('users-length').textContent).toBe('0'));
    expect(apiClient.get).toHaveBeenCalledTimes(2);
  });
});

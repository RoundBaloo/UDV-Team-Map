import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { authApi } from '../api/auth';
import { employeesApi } from '../api/employees';
import { tokenStorage } from '../storage/tokenStorage';

/* =======================
   МОКИ
======================= */

jest.mock('../api/auth');
jest.mock('../api/employees');
jest.mock('../storage/tokenStorage');

/* =======================
   ТЕСТОВЫЙ КОМПОНЕНТ
======================= */

const TestComponent = () => {
  const {
    user,
    loading,
    error,
    login,
    logout,
    updateUser,
    isAuthenticated,
  } = useAuth();

  return (
    <div>
      <div data-testid="user">
        {user ? user.name : 'null'}
      </div>

      <div data-testid="loading">
        {loading ? 'loading' : 'idle'}
      </div>

      <div data-testid="error">
        {error || 'no-error'}
      </div>

      <div data-testid="auth">
        {isAuthenticated ? 'yes' : 'no'}
      </div>

      <button onClick={() => login('test@udv.com', '123')}>
        login
      </button>

      <button onClick={logout}>
        logout
      </button>

      <button
        onClick={() =>
          updateUser({ name: 'Updated User' })
        }
      >
        updateUser
      </button>
    </div>
  );
};

/* =======================
   ХЕЛПЕР РЕНДЕРА
======================= */

const renderWithProvider = () =>
  render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );

/* =======================
   ТЕСТЫ
======================= */

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('без токена: пользователь не авторизован', async () => {
    tokenStorage.getToken.mockReturnValue(null);

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId('auth').textContent).toBe('no');
      expect(screen.getByTestId('loading').textContent).toBe('idle');
    });
  });

  test('login: успешная авторизация', async () => {
    tokenStorage.getToken.mockReturnValue(null);

    authApi.login.mockResolvedValue({
      access_token: 'token',
    });

    authApi.getMe.mockResolvedValue({
      employee_id: 1,
    });

    employeesApi.getEmployee.mockResolvedValue({
      employee_id: 1,
      name: 'Ivan',
    });

    renderWithProvider();

    screen.getByText('login').click();

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('Ivan');
      expect(screen.getByTestId('auth').textContent).toBe('yes');
    });

    expect(tokenStorage.setToken).toHaveBeenCalledWith('token');
  });

  test('logout: очищает пользователя и токен', async () => {
    tokenStorage.getToken.mockReturnValue('token');

    authApi.getMe.mockResolvedValue({
      employee_id: 1,
    });

    employeesApi.getEmployee.mockResolvedValue({
      employee_id: 1,
      name: 'Ivan',
    });

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId('auth').textContent).toBe('yes');
    });

    screen.getByText('logout').click();

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('null');
      expect(screen.getByTestId('auth').textContent).toBe('no');
    });

    expect(tokenStorage.removeToken).toHaveBeenCalled();
  });

  test('updateUser обновляет локальное состояние', async () => {
    tokenStorage.getToken.mockReturnValue('token');

    authApi.getMe.mockResolvedValue({
      employee_id: 1,
    });

    employeesApi.getEmployee.mockResolvedValue({
      employee_id: 1,
      name: 'Initial',
    });

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('Initial');
    });

    screen.getByText('updateUser').click();

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('Updated User');
    });
  });

  test('login: ошибка авторизации', async () => {
    tokenStorage.getToken.mockReturnValue(null);

    authApi.login.mockRejectedValue(
      new Error('Неверный логин или пароль')
    );

    renderWithProvider();

    screen.getByText('login').click();

    await waitFor(() => {
      expect(screen.getByTestId('error').textContent)
        .toBe('Неверный логин или пароль');
      expect(screen.getByTestId('auth').textContent).toBe('no');
    });
  });
});

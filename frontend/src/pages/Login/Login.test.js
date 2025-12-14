import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from './index';
import { useAuth } from '../../services/auth/useAuth';

jest.mock('../../services/auth/useAuth');

describe('Login page', () => {
  const mockLogin = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();

    useAuth.mockReturnValue({
      login: mockLogin,
      error: null,
    });

    global.fetch = jest.fn();
  });

  test('показывает успешный статус API', async () => {
    fetch.mockResolvedValueOnce({ ok: true });

    render(<Login />);

    const status = await screen.findByText('Сервер доступен');
    expect(status).toBeTruthy();
  });

  test('показывает ошибку API при недоступном сервере', async () => {
    fetch.mockRejectedValueOnce(new Error('network'));

    render(<Login />);

    const status = await screen.findByText('Сервер недоступен');
    expect(status).toBeTruthy();
  });

  test('показывает ошибки валидации при пустой форме', async () => {
    fetch.mockResolvedValueOnce({ ok: true });

    const user = userEvent;
    render(<Login />);

    await user.click(screen.getByRole('button', { name: /войти/i }));

    expect(screen.getByText('Email обязателен')).toBeTruthy();
    expect(screen.getByText('Пароль обязателен')).toBeTruthy();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  test('показывает ошибку при некорректном email', async () => {
    fetch.mockResolvedValueOnce({ ok: true });

    const user = userEvent;
    render(<Login />);

    await user.type(
      screen.getByLabelText('Корпоративная почта'),
      'invalid'
    );
    await user.type(
      screen.getByLabelText('Пароль'),
      '123'
    );

    await user.click(screen.getByRole('button', { name: /войти/i }));

    expect(screen.getByText('Введите корректный email')).toBeTruthy();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  test('вызывает login с корректными данными', async () => {
    fetch.mockResolvedValueOnce({ ok: true });
    mockLogin.mockResolvedValueOnce({ success: true });

    const user = userEvent;
    render(<Login />);

    await user.type(
      screen.getByLabelText('Корпоративная почта'),
      'ivanov@udv.com'
    );
    await user.type(
      screen.getByLabelText('Пароль'),
      'secret'
    );

    await user.click(screen.getByRole('button', { name: /войти/i }));

    expect(mockLogin).toHaveBeenCalledWith(
      'ivanov@udv.com',
      'secret'
    );
  });

  test('показывает ошибку авторизации', async () => {
    fetch.mockResolvedValueOnce({ ok: true });
    mockLogin.mockResolvedValueOnce({
      success: false,
      error: 'Неверный логин или пароль',
    });

    const user = userEvent;
    render(<Login />);

    await user.type(
      screen.getByLabelText('Корпоративная почта'),
      'ivanov@udv.com'
    );
    await user.type(
      screen.getByLabelText('Пароль'),
      'wrong'
    );

    await user.click(screen.getByRole('button', { name: /войти/i }));

    const error = await screen.findByText('Неверный логин или пароль');
    expect(error).toBeTruthy();
  });

  test('блокирует кнопку при отправке формы', async () => {
    fetch.mockResolvedValueOnce({ ok: true });

    mockLogin.mockImplementation(
      () => new Promise(resolve => setTimeout(
        () => resolve({ success: true }),
        50
      ))
    );

    const user = userEvent;
    render(<Login />);

    await user.type(
      screen.getByLabelText('Корпоративная почта'),
      'ivanov@udv.com'
    );
    await user.type(
      screen.getByLabelText('Пароль'),
      'secret'
    );

    await user.click(screen.getByRole('button', { name: /войти/i }));

    const button = screen.getByRole('button', { name: 'Вход...' });
    expect(button.disabled).toBe(true);
  });
});

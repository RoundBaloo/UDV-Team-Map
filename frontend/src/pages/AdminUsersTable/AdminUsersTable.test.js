import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AdminUsersTable from './index';
import '@testing-library/jest-dom';

jest.mock('../../components/common/Header', () => () => (
  <div data-testid="mock-header">Header</div>
));

jest.mock('../../components/admin/EditUserModal/index', () => ({
  __esModule: true,
  default: ({ userId, isOpen, onClose }) =>
    isOpen ? (
      <div data-testid="mock-edit-user-modal" onClick={onClose}>
        Modal userId:{userId}
      </div>
    ) : null,
}));

jest.mock('../../components/admin/AdminTable', () => ({
  __esModule: true,
  default: ({ data = [], renderActions }) => (
    <div data-testid="mock-admin-table">
      {data.map((row) => (
        <div key={row.id} data-testid={`row-${row.id}`}>
          <span data-testid={`row-email-${row.id}`}>{row.email}</span>
          <span data-testid={`row-actions-${row.id}`}>{renderActions?.(row)}</span>
        </div>
      ))}
    </div>
  ),
}));

jest.mock('../../hooks/useAdminUsers', () => ({
  useAdminUsers: jest.fn(),
}));

const { useAdminUsers } = require('../../hooks/useAdminUsers');

describe('AdminUsersTable (расширенные тесты)', () => {
  const mockUsers = [
    {
      id: 1,
      first_name: 'Ivan',
      last_name: 'Ivanov',
      middle_name: 'I',
      email: 'ivan@example.com',
      title: 'Dev',
      work_city: 'Moscow',
      work_format: 'remote',
      org_unit: { name: 'Unit 1' },
      is_blocked: false,
      status: 'active',
    },
    {
      id: 2,
      first_name: 'Petr',
      last_name: 'Petrov',
      middle_name: null,
      email: 'petr@example.com',
      title: null,
      work_city: null,
      work_format: 'office',
      org_unit: null,
      is_blocked: true,
      status: 'inactive',
    },
  ];

  const mockHandleEdit = jest.fn();
  const mockRefreshUsers = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    useAdminUsers.mockReturnValue({
      users: mockUsers,
      loading: false,
      editingId: null,
      handleEdit: mockHandleEdit,
      refreshUsers: mockRefreshUsers,
    });
  });

  test('рендерит Header, заголовок и пользователей', () => {
    render(<AdminUsersTable />);

    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByText(/Управление пользователями/)).toBeInTheDocument();
    expect(screen.getByText(/Всего пользователей:\s*2/)).toBeInTheDocument();

    expect(screen.getByTestId('row-email-1')).toHaveTextContent('ivan@example.com');
    expect(screen.getByTestId('row-email-2')).toHaveTextContent('petr@example.com');
  });

  test('колонки таблицы рендерят корректные данные и edge cases', () => {
    render(<AdminUsersTable />);

    // ФИО
    expect(screen.getByText('Ivan Ivanov I')).toBeInTheDocument();
    expect(screen.getByText('Petr Petrov')).toBeInTheDocument();

    // Должность
    expect(screen.getByText('Dev')).toBeInTheDocument();
    expect(screen.getAllByText('-').length).toBeGreaterThan(0); // пустые должности

    // Формат работы
    expect(screen.getByText('Удаленно')).toBeInTheDocument();
    expect(screen.getByText('Офис')).toBeInTheDocument();

    // Подразделение
    expect(screen.getByText('Unit 1')).toBeInTheDocument();
    expect(screen.getAllByText('-').length).toBeGreaterThan(0); // пустые подразделения

    // Статус
    expect(screen.getByText('Активен')).toBeInTheDocument();
    expect(screen.getByText('Заблокирован')).toBeInTheDocument();
  });

  test('нажатие "Обновить" вызывает refreshUsers', () => {
    render(<AdminUsersTable />);

    const refreshBtn = screen.getByRole('button', { name: /Обновить/i });
    fireEvent.click(refreshBtn);

    expect(mockRefreshUsers).toHaveBeenCalled();
  });

  test('нажатие "Редактировать" открывает модалку и вызывает handleEdit', async () => {
    render(<AdminUsersTable />);

    const editButton = screen.getByTestId('row-actions-1').querySelector('button');
    fireEvent.click(editButton);

    expect(mockHandleEdit).toHaveBeenCalledWith(mockUsers[0]);

    await waitFor(() => {
      expect(screen.getByTestId('mock-edit-user-modal')).toBeInTheDocument();
      expect(screen.getByTestId('mock-edit-user-modal').textContent).toContain('userId:1');
    });
  });

  test('закрытие модалки сбрасывает selectedUserId', async () => {
    render(<AdminUsersTable />);

    const editButton = screen.getByTestId('row-actions-1').querySelector('button');
    fireEvent.click(editButton);

    const modal = screen.getByTestId('mock-edit-user-modal');
    fireEvent.click(modal); 

    await waitFor(() => {
      expect(screen.queryByTestId('mock-edit-user-modal')).not.toBeInTheDocument();
    });
  });

  test('показывает индикатор загрузки, если loading=true', () => {
    useAdminUsers.mockReturnValue({
      users: [],
      loading: true,
      editingId: null,
      handleEdit: mockHandleEdit,
      refreshUsers: mockRefreshUsers,
    });

    render(<AdminUsersTable />);

    expect(screen.getByText('Загрузка...')).toBeInTheDocument();
    expect(screen.getByText('Загрузка...').className).toContain('loading-indicator');
  });
});

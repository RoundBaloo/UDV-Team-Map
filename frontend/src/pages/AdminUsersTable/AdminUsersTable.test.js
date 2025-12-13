import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AdminUsersTable from './index';
import '@testing-library/jest-dom';

jest.mock('../../components/common/Header', () => () => (
  <div data-testid="mock-header">Header</div>
));

jest.mock('../../components/admin/EditUserModal/index', () => ({
  __esModule: true,
  default: ({ userId, isOpen, onClose, onSaveSuccess }) =>
    isOpen ? (
      <div data-testid="mock-edit-user-modal">
        <div>Modal userId:{userId}</div>
        <button data-testid="mock-modal-close" onClick={onClose}>Close</button>
        <button data-testid="mock-modal-save-success" onClick={onSaveSuccess}>Save Success</button>
      </div>
    ) : null,
}));

jest.mock('../../components/admin/AdminTable', () => ({
  __esModule: true,
  default: ({ data = [], columns = [], renderActions }) => (
    <div data-testid="mock-admin-table">
      {data.map((row) => (
        <div key={row.id} data-testid={`row-${row.id}`}>
          {columns.map((column) => {
            const value = column.render 
              ? column.render(row[column.key], row)
              : row[column.key];
            return (
              <span key={column.key} data-testid={`row-${column.key}-${row.id}`}>
                {value}
              </span>
            );
          })}
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

    // ФИО (формат: last_name first_name middle_name)
    expect(screen.getByText('Ivanov Ivan I')).toBeInTheDocument();
    expect(screen.getByText('Petrov Petr')).toBeInTheDocument();

    // Email (должен быть ссылкой)
    expect(screen.getByText('ivan@example.com')).toBeInTheDocument();
    expect(screen.getByText('petr@example.com')).toBeInTheDocument();

    // Должность
    expect(screen.getByText('Dev')).toBeInTheDocument();
    expect(screen.getAllByText('-').length).toBeGreaterThan(0); // пустые должности

    // Город
    expect(screen.getByText('Moscow')).toBeInTheDocument();
    expect(screen.getAllByText('-').length).toBeGreaterThan(0); // пустые города

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

    expect(screen.getByTestId('mock-edit-user-modal')).toBeInTheDocument();
    
    const closeButton = screen.getByTestId('mock-modal-close');
    fireEvent.click(closeButton); 

    await waitFor(() => {
      expect(screen.queryByTestId('mock-edit-user-modal')).not.toBeInTheDocument();
    });
  });

  test('handleSaveSuccess вызывает refreshUsers после сохранения', () => {
    render(<AdminUsersTable />);

    // Открываем модалку
    const editButton = screen.getByTestId('row-actions-1').querySelector('button');
    fireEvent.click(editButton);

    // Проверяем, что модалка открыта
    expect(screen.getByTestId('mock-edit-user-modal')).toBeInTheDocument();
    
    // Вызываем onSaveSuccess через кнопку в моке
    const saveSuccessButton = screen.getByTestId('mock-modal-save-success');
    fireEvent.click(saveSuccessButton);
    
    // Проверяем, что refreshUsers был вызван
    expect(mockRefreshUsers).toHaveBeenCalledTimes(1);
  });

  test('рендерит все колонки с правильными данными', () => {
    render(<AdminUsersTable />);

    // Проверяем, что все колонки рендерятся через data-testid
    const row1 = screen.getByTestId('row-1');
    expect(row1).toBeInTheDocument();

    // Проверяем ФИО колонку (name)
    expect(screen.getByTestId('row-name-1')).toBeInTheDocument();
    expect(screen.getByTestId('row-name-1')).toHaveTextContent('Ivanov Ivan I');

    // Проверяем email колонку
    expect(screen.getByTestId('row-email-1')).toBeInTheDocument();
    
    // Проверяем legal_entity колонку
    expect(screen.getByTestId('row-legal_entity-1')).toBeInTheDocument();
    
    // Проверяем title колонку
    expect(screen.getByTestId('row-title-1')).toBeInTheDocument();
    expect(screen.getByTestId('row-title-1')).toHaveTextContent('Dev');
    
    // Проверяем work_city колонку
    expect(screen.getByTestId('row-work_city-1')).toBeInTheDocument();
    expect(screen.getByTestId('row-work_city-1')).toHaveTextContent('Moscow');
    
    // Проверяем work_format колонку
    expect(screen.getByTestId('row-work_format-1')).toBeInTheDocument();
    expect(screen.getByTestId('row-work_format-1')).toHaveTextContent('Удаленно');
    
    // Проверяем org_unit колонку
    expect(screen.getByTestId('row-org_unit-1')).toBeInTheDocument();
    expect(screen.getByTestId('row-org_unit-1')).toHaveTextContent('Unit 1');
    
    // Проверяем status колонку
    expect(screen.getByTestId('row-status-1')).toBeInTheDocument();
    expect(screen.getByTestId('row-status-1')).toHaveTextContent('Активен');
  });

  test('рендерит edge cases для колонок (null, undefined, пустые значения)', () => {
    render(<AdminUsersTable />);

    const row2 = screen.getByTestId('row-2');
    expect(row2).toBeInTheDocument();

    // Проверяем ФИО без middle_name
    expect(screen.getByTestId('row-name-2')).toHaveTextContent('Petrov Petr');

    // Проверяем title = null (должно быть '-')
    expect(screen.getByTestId('row-title-2')).toHaveTextContent('-');

    // Проверяем work_city = null (должно быть '-')
    expect(screen.getByTestId('row-work_city-2')).toHaveTextContent('-');

    // Проверяем org_unit = null (должно быть '-')
    expect(screen.getByTestId('row-org_unit-2')).toHaveTextContent('-');

    // Проверяем status для заблокированного пользователя
    expect(screen.getByTestId('row-status-2')).toHaveTextContent('Заблокирован');
  });

  test('рендерит статус для неактивного пользователя (не заблокированного)', () => {
    const inactiveUser = {
      id: 3,
      first_name: 'Test',
      last_name: 'User',
      middle_name: null,
      email: 'test@example.com',
      title: null,
      work_city: null,
      work_format: 'office',
      org_unit: null,
      is_blocked: false,
      status: 'inactive',
    };

    useAdminUsers.mockReturnValue({
      users: [inactiveUser],
      loading: false,
      editingId: null,
      handleEdit: mockHandleEdit,
      refreshUsers: mockRefreshUsers,
    });

    render(<AdminUsersTable />);

    // Проверяем статус для неактивного пользователя (должно быть 'inactive')
    expect(screen.getByTestId('row-status-3')).toHaveTextContent('inactive');
  });

  test('рендерит статус для пользователя без статуса', () => {
    const userWithoutStatus = {
      id: 4,
      first_name: 'No',
      last_name: 'Status',
      middle_name: null,
      email: 'nostatus@example.com',
      title: null,
      work_city: null,
      work_format: 'office',
      org_unit: null,
      is_blocked: false,
      status: null,
    };

    useAdminUsers.mockReturnValue({
      users: [userWithoutStatus],
      loading: false,
      editingId: null,
      handleEdit: mockHandleEdit,
      refreshUsers: mockRefreshUsers,
    });

    render(<AdminUsersTable />);

    // Проверяем статус для пользователя без статуса (должно быть '-')
    expect(screen.getByTestId('row-status-4')).toHaveTextContent('-');
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

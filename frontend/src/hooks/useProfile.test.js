import React from 'react';
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react';

// Моки внешних модулей
jest.mock('react-router-dom', () => ({ useParams: jest.fn() }));
jest.mock('../services/auth/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('../services/api/employees', () => ({
  employeesApi: {
    getCurrentEmployee: jest.fn(),
    getEmployee: jest.fn(),
    updateMe: jest.fn(),
  },
}));
jest.mock('../services/api/photoModeration', () => ({
  photoModerationApi: {
    getMyModerationStatus: jest.fn(),
  },
}));

// Импортируем то, что тестируем
const { useParams } = require('react-router-dom');
const { useAuth } = require('../services/auth/useAuth');
const { employeesApi } = require('../services/api/employees');
const { photoModerationApi } = require('../services/api/photoModeration');
const { useProfile } = require('./useProfile');

// Моки для mockData
jest.mock('../utils/mockData', () => ({
  mockEmployee: {
    id: 1,
    first_name: 'Иван',
    last_name: 'Иванов',
    middle_name: 'Иванович',
    email: 'ivanov@udv-group.ru',
    title: 'Разработчик',
    status: 'active',
    work_phone: '+7 (999) 123-45-67',
    mattermost_handle: '@ivanov',
    work_city: 'Москва',
    work_format: 'office',
    time_zone: 'Europe/Moscow',
    bio: 'Опытный разработчик',
    hire_date: '2020-01-15',
    is_admin: false,
    is_blocked: false,
    last_login_at: '2024-01-15T10:30:00Z',
    photo: null,
    manager: null,
    org_unit: null,
    employee_id: 1,
    legal_entity: 'UDV Group',
    skills: ['React', 'JavaScript'],
    grade: 'Middle',
    telegram: '@ivanov',
  },
  mockCurrentUser: {
    id: 10,
    employee_id: 10,
    first_name: 'Текущий',
    last_name: 'Пользователь',
    email: 'current@udv-group.ru',
    title: 'Тимлид',
  },
  getEmployeesByUnitId: {
    1: [
      {
        id: 1,
        employee_id: 1,
        first_name: 'Иван',
        last_name: 'Иванов',
        email: 'ivanov@udv-group.ru',
      },
      {
        id: 2,
        employee_id: 2,
        first_name: 'Петр',
        last_name: 'Петров',
        email: 'petrov@udv-group.ru',
      },
    ],
  },
}));

// Компонент-обёртка для тестирования хука через render
function TestComponent() {
  const p = useProfile();

  return (
    <div>
      <div data-testid="loading">{String(p.loading)}</div>
      <div data-testid="profile">{JSON.stringify(p.profile)}</div>
      <div data-testid="error">{p.error}</div>
      <div data-testid="editing">{String(p.editing)}</div>
      <div data-testid="editedData">{JSON.stringify(p.editedData)}</div>
      <div data-testid="saving">{String(p.saving)}</div>
      <div data-testid="moderationStatus">{JSON.stringify(p.moderationStatus)}</div>
      <div data-testid="uploadingAvatar">{String(p.uploadingAvatar)}</div>
      <div data-testid="isOwnProfile">{String(p.isOwnProfile)}</div>
      <div data-testid="profileId">{String(p.profileId)}</div>
      <div data-testid="avatarModerationStatus">{String(p.getAvatarModerationStatus())}</div>

      <button data-testid="handleEdit" onClick={p.handleEdit}>edit</button>
      <button data-testid="handleCancel" onClick={p.handleCancel}>cancel</button>
      <button data-testid="handleSave" onClick={() => p.handleSave()}>save</button>
      <button data-testid="handleFieldChange" onClick={() => p.handleFieldChange('bio', 'new-bio')}>fieldChange</button>

      <button data-testid="avatarStart" onClick={p.handleAvatarUploadStart}>avatarStart</button>
      <button data-testid="avatarSuccess" onClick={() => p.handleAvatarUploadSuccess({ status: 'approved' })}>avatarSuccess</button>
      <button data-testid="avatarError" onClick={() => p.handleAvatarUploadError('errmsg')}>avatarError</button>
    </div>
  );
}

describe('useProfile hook', () => {
  const CURRENT_USER = { id: 1, employee_id: 10 };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('loads own profile and moderation status (success)', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    const current = { id: 10, employee_id: 10, first_name: 'Me' };
    employeesApi.getCurrentEmployee.mockResolvedValueOnce(current);
    photoModerationApi.getMyModerationStatus.mockResolvedValueOnce({ 
      has_request: true, 
      last: { status: 'approved' } 
    });

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(JSON.parse(screen.getByTestId('profile').textContent)).toEqual(current);
    expect(JSON.parse(screen.getByTestId('moderationStatus').textContent)).toEqual({ 
      has_request: true, 
      last: { status: 'approved' } 
    });
    expect(screen.getByTestId('isOwnProfile').textContent).toBe('true');
    expect(screen.getByTestId('profileId').textContent).toBe('10');
    expect(screen.getByTestId('avatarModerationStatus').textContent).toBe('approved');
  });

  test('moderation API fails -> default moderationStatus set', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    employeesApi.getCurrentEmployee.mockResolvedValueOnce({ id: 10, employee_id: 10 });
    photoModerationApi.getMyModerationStatus.mockRejectedValueOnce(new Error('mod-fail'));

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(JSON.parse(screen.getByTestId('moderationStatus').textContent)).toEqual({ 
      has_request: false, 
      last: null 
    });
    expect(screen.getByTestId('avatarModerationStatus').textContent).toBe('null');
  });

  test('loads other profile via getEmployee', async () => {
    useParams.mockReturnValue({ id: '20' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    const other = { id: 20, first_name: 'Other' };
    employeesApi.getEmployee.mockResolvedValueOnce(other);

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(JSON.parse(screen.getByTestId('profile').textContent)).toEqual(other);
    expect(screen.getByTestId('isOwnProfile').textContent).toBe('false');
  });

  test('handleEdit and handleCancel work', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    employeesApi.getCurrentEmployee.mockResolvedValueOnce({ id: 10, employee_id: 10 });
    photoModerationApi.getMyModerationStatus.mockResolvedValueOnce({ has_request: false, last: null });

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    act(() => {
      fireEvent.click(screen.getByTestId('handleEdit'));
    });

    expect(screen.getByTestId('editing').textContent).toBe('true');
    const edited = JSON.parse(screen.getByTestId('editedData').textContent);
    expect(edited).toMatchObject({ id: 10 });

    act(() => {
      fireEvent.click(screen.getByTestId('handleCancel'));
    });

    expect(screen.getByTestId('editing').textContent).toBe('false');
    expect(screen.getByTestId('editedData').textContent).toBe('{}');
  });

  test('handleSave success updates profile and sets success message', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    const initial = { id: 10, employee_id: 10, bio: 'old' };
    employeesApi.getCurrentEmployee.mockResolvedValueOnce(initial);
    photoModerationApi.getMyModerationStatus.mockResolvedValueOnce({ has_request: false, last: null });

    const updated = { id: 10, employee_id: 10, bio: 'updated' };
    employeesApi.updateMe.mockResolvedValueOnce(updated);

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    act(() => fireEvent.click(screen.getByTestId('handleEdit')));
    act(() => fireEvent.click(screen.getByTestId('handleFieldChange')));

    // Используем act для асинхронных операций
    await act(async () => {
      fireEvent.click(screen.getByTestId('handleSave'));
      // Даем время для выполнения промиса
      await Promise.resolve();
    });

    // Ждем завершения сохранения
    await waitFor(() => expect(screen.getByTestId('saving').textContent).toBe('false'));

    const profileAfter = JSON.parse(screen.getByTestId('profile').textContent);
    expect(profileAfter.bio).toBe('updated');
    expect(screen.getByTestId('editing').textContent).toBe('false');
    expect(screen.getByTestId('error').textContent).toBe('Данные успешно сохранены!');
  });

  test('handleSave failure sets error', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    employeesApi.getCurrentEmployee.mockResolvedValueOnce({ id: 10, employee_id: 10 });
    photoModerationApi.getMyModerationStatus.mockResolvedValueOnce({ has_request: false, last: null });

    employeesApi.updateMe.mockRejectedValueOnce(new Error('save-fail'));

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    act(() => fireEvent.click(screen.getByTestId('handleEdit')));

    await act(async () => {
      fireEvent.click(screen.getByTestId('handleSave'));
      await Promise.resolve();
    });

    await waitFor(() => expect(screen.getByTestId('saving').textContent).toBe('false'));
    expect(screen.getByTestId('error').textContent).toBe('Ошибка при сохранении профиля');
  });

  test('handleSave does nothing if not own profile', async () => {
    useParams.mockReturnValue({ id: '20' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    const other = { id: 20, first_name: 'Other' };
    employeesApi.getEmployee.mockResolvedValueOnce(other);

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    act(() => fireEvent.click(screen.getByTestId('handleSave')));

    expect(employeesApi.updateMe).not.toHaveBeenCalled();
    expect(screen.getByTestId('saving').textContent).toBe('false');
  });

  test('handleFieldChange updates editedData', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    employeesApi.getCurrentEmployee.mockResolvedValueOnce({ id: 10, employee_id: 10 });
    photoModerationApi.getMyModerationStatus.mockResolvedValueOnce({ has_request: false, last: null });

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    act(() => fireEvent.click(screen.getByTestId('handleEdit')));
    act(() => fireEvent.click(screen.getByTestId('handleFieldChange')));

    const edited = JSON.parse(screen.getByTestId('editedData').textContent);
    expect(edited.bio).toBe('new-bio');
  });

  test('avatar upload handlers update moderationStatus and error correctly', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    employeesApi.getCurrentEmployee.mockResolvedValueOnce({ id: 10, employee_id: 10 });
    photoModerationApi.getMyModerationStatus.mockResolvedValueOnce({ has_request: true, last: { status: 'approved' } });

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    // start upload
    act(() => fireEvent.click(screen.getByTestId('avatarStart')));
    expect(screen.getByTestId('uploadingAvatar').textContent).toBe('true');

    // success
    act(() => fireEvent.click(screen.getByTestId('avatarSuccess')));
    expect(screen.getByTestId('uploadingAvatar').textContent).toBe('false');
    expect(JSON.parse(screen.getByTestId('moderationStatus').textContent).has_request).toBe(true);
    expect(screen.getByTestId('error').textContent).toBe('Фото успешно загружено и отправлено на модерацию!');

    // error
    act(() => fireEvent.click(screen.getByTestId('avatarError')));
    expect(screen.getByTestId('uploadingAvatar').textContent).toBe('false');
    expect(screen.getByTestId('error').textContent).toBe('Ошибка загрузки фото: errmsg');
  });

  test('getAvatarModerationStatus returns correct status', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: CURRENT_USER });

    employeesApi.getCurrentEmployee.mockResolvedValueOnce({ id: 10, employee_id: 10 });
    photoModerationApi.getMyModerationStatus.mockResolvedValueOnce({ 
      has_request: true, 
      last: { status: 'pending' } 
    });

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    expect(screen.getByTestId('avatarModerationStatus').textContent).toBe('pending');
  });

  test('profileId calculation works correctly', async () => {
    // Тестируем разные варианты profileId
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: { employee_id: 5, id: 5 } });

    employeesApi.getCurrentEmployee.mockResolvedValueOnce({ id: 5, employee_id: 5 });
    photoModerationApi.getMyModerationStatus.mockResolvedValueOnce({ has_request: false, last: null });

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('profileId').textContent).toBe('5'));
  });

  test('empty user case', async () => {
    useParams.mockReturnValue({ id: 'me' });
    useAuth.mockReturnValue({ user: null });

    await act(async () => {
      render(<TestComponent />);
    });

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));
    expect(screen.getByTestId('error').textContent).toBe('Пользователь не найден');
  });
});
import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Profile from './index';

jest.mock('../../components/common/Header', () => () => <div data-testid="mock-header">Header</div>);

jest.mock('../../components/profile/ProfileHeader', () => ({ onEdit, onSave, onCancel }) => (
  <div data-testid="mock-profile-header">
    <button data-testid="edit-btn" onClick={onEdit}>Edit</button>
    <button data-testid="save-btn" onClick={onSave}>Save</button>
    <button data-testid="cancel-btn" onClick={onCancel}>Cancel</button>
  </div>
));
jest.mock('../../components/profile/ProfileContacts', () => () => <div data-testid="mock-profile-contacts" />);
jest.mock('../../components/profile/ProfilePersonal', () => () => <div data-testid="mock-profile-personal" />);
jest.mock('../../components/profile/ProfileLocation', () => () => <div data-testid="mock-profile-location" />);

jest.mock('../../hooks/useProfile', () => ({
  useProfile: jest.fn(),
}));

const { useProfile } = require('../../hooks/useProfile');

describe('Profile page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('показывает loading state', () => {
    useProfile.mockReturnValue({
      loading: true,
    });

    render(<Profile />);
    expect(screen.getByText(/Загрузка профиля/i)).toBeInTheDocument();
    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
  });

  test('показывает ErrorState, если profile отсутствует', () => {
    useProfile.mockReturnValue({
      loading: false,
      profile: null,
      error: 'Ошибка загрузки профиля',
    });

    render(<Profile />);
    expect(screen.getByText(/Ошибка загрузки профиля/i)).toBeInTheDocument();
  });

  test('рендерит все компоненты профиля, если profile загружен', () => {
    useProfile.mockReturnValue({
      loading: false,
      profile: { id: 1, first_name: 'Ivan' },
      editedData: {},
      editing: false,
      error: null,
      isOwnProfile: true,
      moderationStatus: 'approved',
      uploadingAvatar: false,
      handleEdit: jest.fn(),
      handleCancel: jest.fn(),
      handleSave: jest.fn(),
      handleFieldChange: jest.fn(),
      handleAvatarUploadStart: jest.fn(),
      handleAvatarUploadSuccess: jest.fn(),
      handleAvatarUploadError: jest.fn(),
      getAvatarModerationStatus: () => 'approved',
    });

    render(<Profile />);
    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-profile-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-profile-contacts')).toBeInTheDocument();
    expect(screen.getByTestId('mock-profile-personal')).toBeInTheDocument();
    expect(screen.getByTestId('mock-profile-location')).toBeInTheDocument();
  });

  test('редактирование и кнопки вызывают обработчики', () => {
    const handleEdit = jest.fn();
    const handleSave = jest.fn();
    const handleCancel = jest.fn();

    useProfile.mockReturnValue({
      loading: false,
      profile: { id: 1 },
      editedData: {},
      editing: true,
      error: null,
      isOwnProfile: true,
      moderationStatus: 'approved',
      uploadingAvatar: false,
      handleEdit,
      handleCancel,
      handleSave,
      handleFieldChange: jest.fn(),
      handleAvatarUploadStart: jest.fn(),
      handleAvatarUploadSuccess: jest.fn(),
      handleAvatarUploadError: jest.fn(),
      getAvatarModerationStatus: () => 'approved',
    });

    render(<Profile />);

    fireEvent.click(screen.getByTestId('edit-btn'));
    expect(handleEdit).toHaveBeenCalled();

    fireEvent.click(screen.getByTestId('save-btn'));
    expect(handleSave).toHaveBeenCalled();

    fireEvent.click(screen.getByTestId('cancel-btn'));
    expect(handleCancel).toHaveBeenCalled();
  });

  test('отображает ErrorAlert, если есть ошибка', () => {
    useProfile.mockReturnValue({
      loading: false,
      profile: { id: 1 },
      editedData: {},
      editing: false,
      error: 'Произошла ошибка',
      isOwnProfile: true,
      moderationStatus: 'approved',
      uploadingAvatar: false,
      handleEdit: jest.fn(),
      handleCancel: jest.fn(),
      handleSave: jest.fn(),
      handleFieldChange: jest.fn(),
      handleAvatarUploadStart: jest.fn(),
      handleAvatarUploadSuccess: jest.fn(),
      handleAvatarUploadError: jest.fn(),
      getAvatarModerationStatus: () => 'approved',
    });

    render(<Profile />);
    expect(screen.getByText(/Произошла ошибка/i)).toBeInTheDocument();
  });
});

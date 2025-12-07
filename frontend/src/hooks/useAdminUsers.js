// hooks/useAdminUsers.js
import { useState, useEffect } from 'react';
import { apiClient } from '../services/api/apiClient';
import { API_ENDPOINTS } from '../utils/constants';

export const useAdminUsers = () => {
  const [state, setState] = useState({
    users: [],
    loading: true,
    editingId: null,
    editedUser: {},
    error: null,
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Используем apiClient для запроса
      const data = await apiClient.get(API_ENDPOINTS.EMPLOYEES.LIST);
      
      // Преобразуем данные из API в формат таблицы
      const transformedUsers = data.map(user => ({
        id: user.employee_id,  // используем employee_id как id
        email: user.email,
        first_name: user.first_name,
        middle_name: user.middle_name,
        last_name: user.last_name,
        title: user.title,
        status: user.status,
        work_city: user.work_city,
        work_format: user.work_format,
        time_zone: user.time_zone,
        work_phone: user.work_phone,
        mattermost_handle: user.mattermost_handle,
        telegram_handle: user.telegram_handle,
        birth_date: user.birth_date,
        hire_date: user.hire_date,
        bio: user.bio,
        skill_ratings: user.skill_ratings,
        is_admin: user.is_admin,
        is_blocked: user.is_blocked,
        last_login_at: user.last_login_at,
        photo: user.photo,
        manager: user.manager,
        org_unit: user.org_unit,
        // Добавляем поле для сортировки по имени
        name: `${user.last_name || ''} ${user.first_name || ''} ${user.middle_name || ''}`.trim(),
      }));
      
      setState(prev => ({ 
        ...prev, 
        users: transformedUsers, 
        loading: false,
      }));
    } catch (error) {
      console.error('Error loading users:', error);
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error.message,
        users: [],
      }));
    }
  };

  const handleEdit = user => {
    setState(prev => ({
      ...prev,
      editingId: user.id,
      editedUser: {
        ...user,
        work_city: user.work_city || '',
        work_format: user.work_format || 'office',
      },
    }));
  };

  const handleSave = async id => {
    try {
      // Подготовка данных для обновления
      const updateData = {
        work_city: state.editedUser.work_city || null,
        work_format: state.editedUser.work_format || 'office',
      };
      
      // Используем apiClient для обновления пользователя
      const endpoint = API_ENDPOINTS.EMPLOYEES.DETAIL.replace('{employee_id}', id);
      await apiClient.patch(endpoint, updateData);
      
      // Обновляем локальное состояние после успешного сохранения
      setState(prev => ({
        ...prev,
        users: prev.users.map(user => 
          user.id === id ? { ...user, ...prev.editedUser } : user
        ),
        editingId: null,
        editedUser: {},
      }));
      
    } catch (error) {
      console.error('Error saving user:', error);
      setState(prev => ({ ...prev, error: error.message }));
      // Можно добавить уведомление об ошибке
      alert('Ошибка при сохранении изменений: ' + error.message);
    }
  };

  const handleCancel = () => {
    setState(prev => ({
      ...prev,
      editingId: null,
      editedUser: {},
    }));
  };

  const handleFieldChange = (field, value) => {
    setState(prev => ({
      ...prev,
      editedUser: { ...prev.editedUser, [field]: value },
    }));
  };

  // Функция для принудительного обновления данных
  const refreshUsers = () => {
    loadUsers();
  };

  return {
    ...state,
    handleEdit,
    handleSave,
    handleCancel,
    handleFieldChange,
    refreshUsers,
  };
};
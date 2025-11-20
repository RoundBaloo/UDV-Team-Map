import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../services/auth/useAuth';
import { employeesApi } from '../services/api/employees';
import { photoModerationApi } from '../services/api/photoModeration';
import { mockEmployee, mockCurrentUser, getEmployeesByUnitId } from '../utils/mockData';

export const useProfile = () => {
  const { id } = useParams();
  const { user: currentAuthUser } = useAuth();
  
  const [state, setState] = useState({
    profile: null,
    editing: false,
    editedData: {},
    loading: true,
    saving: false,
    error: null,
    moderationStatus: null,
    uploadingAvatar: false,
  });

  const getProfileId = useCallback(() => {
    if (!id || id === 'me') {
      return currentAuthUser?.employee_id || currentAuthUser?.id;
    }
    return parseInt(id);
  }, [id, currentAuthUser]);

  const profileId = getProfileId();
  const isOwnProfile = !id || id === 'me' || id === (currentAuthUser?.employee_id?.toString() || currentAuthUser?.id?.toString());

  useEffect(() => {
    if (!isOwnProfile) return;

    let isMounted = true;
    
    const loadModerationStatus = async () => {
      try {
        const status = await photoModerationApi.getMyModerationStatus();
        if (isMounted) {
          setState(prev => ({ ...prev, moderationStatus: status }));
        }
      } catch (err) {
        if (isMounted) {
          setState(prev => ({
            ...prev,
            moderationStatus: { has_request: false, last: null },
          }));
        }
      }
    };

    loadModerationStatus();

    return () => {
      isMounted = false;
    };
  }, [isOwnProfile]);

  useEffect(() => {
    if (!profileId) {
      setState(prev => ({ ...prev, error: 'Пользователь не найден', loading: false }));
      return;
    }

    let isMounted = true;

    const loadProfile = async () => {
      try {
        setState(prev => ({ ...prev, loading: true }));
        
        let profileData = await loadProfileData(profileId, isOwnProfile, currentAuthUser);

        if (isMounted) {
          setState(prev => ({ ...prev, profile: profileData }));
        }
      } catch (err) {
        const fallbackProfile = getFallbackProfile(profileId, currentAuthUser);
        setState(prev => ({ 
          ...prev, 
          error: 'Не удалось загрузить профиль',
          profile: fallbackProfile,
        }));
      } finally {
        if (isMounted) {
          setState(prev => ({ ...prev, loading: false }));
        }
      }
    };

    loadProfile();

    return () => {
      isMounted = false;
    };
  }, [profileId, currentAuthUser, isOwnProfile]);

  const loadProfileData = async (profileId, isOwnProfile, currentAuthUser) => {
    try {
      if (isOwnProfile) {
        return await employeesApi.getCurrentEmployee();
      } else {
        return await employeesApi.getEmployee(profileId);
      }
    } catch (apiError) {
      return getMockProfileData(profileId, isOwnProfile, currentAuthUser);
    }
  };

  const getMockProfileData = (profileId, isOwnProfile, currentAuthUser) => {
    const allMockEmployees = [];
    Object.values(getEmployeesByUnitId).forEach(employees => {
      allMockEmployees.push(...employees);
    });
    
    const mockEmployeeData = allMockEmployees.find(emp => 
      emp.employee_id === profileId || emp.id === profileId
    );
    
    if (mockEmployeeData) {
      return {
        ...mockEmployeeData,
        legal_entity: mockEmployeeData.legal_entity || 'UDV Group',
        skills: mockEmployeeData.skills || ['React', 'JavaScript', 'TypeScript'],
        grade: mockEmployeeData.grade || 'Middle',
        telegram: mockEmployeeData.telegram || '@username',
      };
    }
    
    if (isOwnProfile && profileId === (currentAuthUser?.employee_id || currentAuthUser?.id)) {
      return {
        ...mockCurrentUser,
        employee_id: profileId,
        id: profileId,
        legal_entity: 'UDV Group',
        skills: ['React', 'JavaScript', 'Team Leadership'],
        grade: 'Senior',
        telegram: '@teamlead',
      };
    }
    
    return {
      ...mockEmployee,
      employee_id: profileId,
      id: profileId,
      first_name: 'Сотрудник',
      last_name: `#${profileId}`,
      email: `user${profileId}@udv-group.ru`,
      title: 'Сотрудник',
      legal_entity: 'UDV Group',
      skills: ['Навык 1', 'Навык 2'],
      grade: 'Junior',
      telegram: '@user',
    };
  };

  const getFallbackProfile = (profileId, currentAuthUser) => {
    const allMockEmployees = [];
    Object.values(getEmployeesByUnitId).forEach(employees => {
      allMockEmployees.push(...employees);
    });
    
    const mockEmployeeData = allMockEmployees.find(emp => 
      emp.employee_id === profileId || emp.id === profileId
    );
    
    return mockEmployeeData || {
      ...mockEmployee,
      employee_id: profileId,
      id: profileId,
      legal_entity: 'UDV Group',
      skills: [],
      grade: '',
      telegram: '',
    };
  };

  const handleEdit = () => {
    setState(prev => ({ 
      ...prev, 
      editedData: prev.profile, 
      editing: true, 
      error: null,
    }));
  };

  const handleCancel = () => {
    setState(prev => ({ 
      ...prev, 
      editedData: {}, 
      editing: false, 
      error: null,
    }));
  };

  const handleSave = async () => {
    if (!isOwnProfile || !(currentAuthUser?.employee_id || currentAuthUser?.id)) return;

    setState(prev => ({ ...prev, saving: true, error: null }));

    try {
      const updateData = {
        bio: state.editedData.bio || null,
        work_phone: state.editedData.work_phone || null,
        mattermost_handle: state.editedData.mattermost_handle || null,
        work_city: state.editedData.work_city || null,
        work_format: state.editedData.work_format || null,
        time_zone: state.editedData.time_zone || null,
      };

      const result = await employeesApi.updateMe(updateData);
      
      setState(prev => ({
        ...prev,
        profile: result,
        editing: false,
        editedData: {},
        error: 'Данные успешно сохранены!',
      }));
      
    } catch (err) {
      console.error('Save error:', err);
      setState(prev => ({ ...prev, error: 'Ошибка при сохранении профиля' }));
    } finally {
      setState(prev => ({ ...prev, saving: false }));
    }
  };

  const handleFieldChange = (fieldName, value) => {
    setState(prev => ({
      ...prev,
      editedData: { ...prev.editedData, [fieldName]: value },
    }));
  };

  const handleAvatarUploadStart = () => {
    setState(prev => ({ ...prev, uploadingAvatar: true, error: null }));
  };

  const handleAvatarUploadSuccess = moderationItem => {
    setState(prev => ({
      ...prev,
      uploadingAvatar: false,
      moderationStatus: { has_request: true, last: moderationItem },
      error: 'Фото успешно загружено и отправлено на модерацию!',
    }));
  };

  const handleAvatarUploadError = errorMessage => {
    setState(prev => ({
      ...prev,
      uploadingAvatar: false,
      error: `Ошибка загрузки фото: ${errorMessage}`,
    }));
  };

  const getAvatarModerationStatus = () => {
    if (!state.moderationStatus || !state.moderationStatus.has_request) {
      return null;
    }
    return state.moderationStatus.last?.status || null;
  };

  return {
    ...state,
    isOwnProfile,
    profileId,
    handleEdit,
    handleCancel,
    handleSave,
    handleFieldChange,
    handleAvatarUploadStart,
    handleAvatarUploadSuccess,
    handleAvatarUploadError,
    getAvatarModerationStatus,
  };
};
import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../services/auth/useAuth';
import { employeesApi } from '../../services/api/employees';
import { photoModerationApi } from '../../services/api/photoModeration'; 
import { mockEmployee, mockCurrentUser, getEmployeesByUnitId } from '../../utils/mockData';
import Header from '../../components/common/Header';
import ProfileField from '../../components/profile/ProfileField';
import AvatarUpload from '../../components/profile/AvatarUpload';
import ProfileActions from '../../components/profile/ProfileActions';
import './Profile.css';

const Profile = () => {
  const { id } = useParams();
  const { user: currentAuthUser, updateUserProfile } = useAuth();
  
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editedData, setEditedData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [moderationStatus, setModerationStatus] = useState(null);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);

  const getProfileId = useCallback(() => {
    if (!id || id === 'me') {
      return currentAuthUser?.employee_id || currentAuthUser?.id;
    }
    return parseInt(id);
  }, [id, currentAuthUser]);

  const profileId = getProfileId();
  const isOwnProfile = !id || id === 'me' || id === (currentAuthUser?.employee_id?.toString() || currentAuthUser?.id?.toString());

  // Загружаем статус модерации для своего профиля - только один раз
  useEffect(() => {
    if (!isOwnProfile) return;

    let isMounted = true;
    
    const loadModerationStatus = async () => {
      try {
        const status = await photoModerationApi.getMyModerationStatus();
        if (isMounted) {
          setModerationStatus(status);
        }
      } catch (err) {
        if (isMounted) {
          setModerationStatus({
            has_request: false,
            last: null,
          });
        }
      }
    };

    loadModerationStatus();

    return () => {
      isMounted = false;
    };
  }, [isOwnProfile]);

  // Загружаем профиль - только один раз
  useEffect(() => {
    if (!profileId) {
      setError('Пользователь не найден');
      setLoading(false);
      return;
    }

    let isMounted = true;

    const loadProfile = async () => {
      try {
        setLoading(true);
        
        let profileData;

        try {
          if (isOwnProfile) {
            profileData = await employeesApi.getCurrentEmployee();
          } else {
            profileData = await employeesApi.getEmployee(profileId);
          }
        } catch (apiError) {
          profileData = null;
        }

        if (!profileData) {
          const allMockEmployees = [];
          Object.values(getEmployeesByUnitId).forEach(employees => {
            allMockEmployees.push(...employees);
          });
          
          const mockEmployeeData = allMockEmployees.find(emp => 
            emp.employee_id === profileId || emp.id === profileId
          );
          
          if (mockEmployeeData) {
            profileData = { 
              ...mockEmployeeData,
              legal_entity: mockEmployeeData.legal_entity || 'UDV Group',
              skills: mockEmployeeData.skills || ['React', 'JavaScript', 'TypeScript'],
              grade: mockEmployeeData.grade || 'Middle',
              telegram: mockEmployeeData.telegram || '@username',
            };
          } else if (isOwnProfile && profileId === (currentAuthUser?.employee_id || currentAuthUser?.id)) {
            profileData = { 
              ...mockCurrentUser, 
              employee_id: profileId,
              id: profileId,
              legal_entity: 'UDV Group',
              skills: ['React', 'JavaScript', 'Team Leadership'],
              grade: 'Senior',
              telegram: '@teamlead',
            };
          } else {
            profileData = { 
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
          }
        }

        if (isMounted) {
          setProfile(profileData);
        }
      } catch (err) {
        setError('Не удалось загрузить профиль');
        const allMockEmployees = [];
        Object.values(getEmployeesByUnitId).forEach(employees => {
          allMockEmployees.push(...employees);
        });
        const mockEmployeeData = allMockEmployees.find(emp => 
          emp.employee_id === profileId || emp.id === profileId
        );
        setProfile(mockEmployeeData || { 
          ...mockEmployee, 
          employee_id: profileId,
          id: profileId,
          legal_entity: 'UDV Group',
          skills: [],
          grade: '',
          telegram: '',
        });
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadProfile();

    return () => {
      isMounted = false;
    };
  }, [profileId, currentAuthUser, isOwnProfile]);

  const handleEdit = () => {
    setEditedData(profile);
    setEditing(true);
    setError(null);
  };

  const handleCancel = () => {
    setEditedData({});
    setEditing(false);
    setError(null);
  };

  const handleSave = async () => {
    if (!isOwnProfile || !(currentAuthUser?.employee_id || currentAuthUser?.id)) return;

    setSaving(true);
    setError(null);

    try {
      const updateData = {
        bio: editedData.bio || null,
        work_phone: editedData.work_phone || null,
        mattermost_handle: editedData.mattermost_handle || null,
        work_city: editedData.work_city || null,
        work_format: editedData.work_format || null,
        time_zone: editedData.time_zone || null,
      };

      // Для своего профиля используем updateMe, а не updateEmployee
      const result = await employeesApi.updateMe(updateData);
      
      setProfile(result);
      setEditing(false);
      setEditedData({});
      setError('Данные успешно сохранены!');
      
    } catch (err) {
      console.error('Save error:', err);
      setError('Ошибка при сохранении профиля');
    } finally {
      setSaving(false);
    }
  };

  const handleFieldChange = (fieldName, value) => {
    setEditedData(prev => ({
      ...prev,
      [fieldName]: value,
    }));
  };

  const handleAvatarUploadStart = () => {
    setUploadingAvatar(true);
    setError(null);
  };

  const handleAvatarUploadSuccess = (moderationItem) => {
    setUploadingAvatar(false);
    setModerationStatus({
      has_request: true,
      last: moderationItem,
    });
    setError('Фото успешно загружено и отправлено на модерацию!');
  };

  const handleAvatarUploadError = (errorMessage) => {
    setUploadingAvatar(false);
    setError(`Ошибка загрузки фото: ${errorMessage}`);
  };

  const handleAvatarChange = async (file, moderationItem) => {
    console.log('Avatar changed:', file, moderationItem);
  };

  const getAvatarModerationStatus = () => {
    if (!moderationStatus || !moderationStatus.has_request) {
      return null;
    }
    return moderationStatus.last?.status || null;
  };

  const getModerationStatusText = () => {
    if (!moderationStatus || !moderationStatus.has_request) {
      return null;
    }

    const status = moderationStatus.last?.status;
    switch (status) {
    case 'pending':
      return 'На рассмотрении';
    case 'approved':
      return 'Одобрено';
    case 'rejected':
      return 'Отклонено';
    default:
      return 'Неизвестно';
    }
  };

  const workFormatOptions = [
    { value: 'office', label: 'Офис' },
    { value: 'hybrid', label: 'Гибридный' },
    { value: 'remote', label: 'Удаленный' },
  ];

  if (loading) {
    return (
      <div className="profile-page">
        <Header />
        <main className="profile-main">
          <div className="container">
            <div className="loading-placeholder">Загрузка профиля...</div>
          </div>
        </main>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="profile-page">
        <Header />
        <main className="profile-main">
          <div className="container">
            <div className="error-placeholder">
              {error || 'Профиль не найден'}
            </div>
          </div>
        </main>
      </div>
    );
  }

  const displayData = editing ? editedData : profile;

  return (
    <div className="profile-page">
      <Header />
      
      <main className="profile-main">
        <div className="container">
          {error && (
            <div className={`alert ${error.includes('успешно') ? 'alert-success' : 'alert-error'}`}>
              {error}
            </div>
          )}

          <div className="profile-layout">
            {/* Левый столбец - Основная информация и Контакты */}
            <div className="profile-column profile-column--left">
              {/* Плашка с аватаром и ФИО */}
              <div className="profile-card">
                <div className="profile-avatar-section">
                  <AvatarUpload
                    currentAvatar={displayData.photo?.public_url}
                    onAvatarChange={handleAvatarChange}
                    onUploadStart={handleAvatarUploadStart}
                    onUploadSuccess={handleAvatarUploadSuccess}
                    onUploadError={handleAvatarUploadError}
                    disabled={!editing || uploadingAvatar}
                    moderationStatus={getAvatarModerationStatus()}
                  />
                  
                  <div className="profile-name-section">
                    <div className="profile-full-name">
                      <div className="last-name">{displayData.last_name}</div>
                      <div className="first-name">{displayData.first_name}</div>
                      <div className="middle-name">{displayData.middle_name}</div>
                    </div>
                  </div>

                  {isOwnProfile && moderationStatus?.has_request && moderationStatus.last?.status !== 'approved' && (
                    <div className="moderation-info">
                      {moderationStatus.last?.status === 'pending' && (
                        <div className="moderation-status">
                          Статус модерации: <strong>На рассмотрении</strong>
                        </div>
                      )}
                      {moderationStatus.last?.status === 'rejected' && (
                        <div className="moderation-reason">
                          <strong>Фото отклонено:</strong> {moderationStatus.last.reject_reason}
                        </div>
                      )}
                    </div>
                  )} 
                </div>

                <div className="profile-main-info">
                  <div className="profile-info-row">
                    <span className="profile-info-label">Должность:</span>
                    <span className="profile-info-value">{displayData.title}</span>
                  </div>
                  <div className="profile-info-row">
                    <span className="profile-info-label">Юр. лицо:</span>
                    <span className="profile-info-value">{displayData.legal_entity}</span>
                  </div>
                  <div className="profile-info-row">
                    <span className="profile-info-label">Отдел/группа:</span>
                    <span className="profile-info-value">{displayData.org_unit?.name}</span>
                  </div>
                </div>

                <ProfileActions
                  isEditing={editing}
                  onEdit={handleEdit}
                  onSave={handleSave}
                  onCancel={handleCancel}
                  isOwnProfile={isOwnProfile}
                  loading={saving || uploadingAvatar}
                />
              </div>

              {/* Плашка Контакты */}
              <div className="profile-section profile-section--contacts">
                <h3 className="profile-section__title">Контакты</h3>
                <div className="profile-section__content">
                  <div className="contact-row">
                    <span className="contact-label">Mattermost:</span>
                    {editing ? (
                      <ProfileField
                        value={displayData.mattermost_handle}
                        editable={true}
                        editing={editing}
                        onChange={handleFieldChange}
                        fieldName="mattermost_handle"
                        hideLabel={true}
                      />
                    ) : (
                      <span className="contact-value">{displayData.mattermost_handle || '—'}</span>
                    )}
                  </div>
                  <div className="contact-row">
                    <span className="contact-label">Email:</span>
                    <span className="contact-value">{displayData.email}</span>
                  </div>
                  <div className="contact-row">
                    <span className="contact-label">Telegram:</span>
                    <span className="contact-value">{displayData.telegram || '—'}</span>
                  </div>
                  <div className="contact-row">
                    <span className="contact-label">Телефон:</span>
                    {editing ? (
                      <ProfileField
                        value={displayData.work_phone}
                        editable={true}
                        editing={editing}
                        onChange={handleFieldChange}
                        fieldName="work_phone"
                        hideLabel={true}
                      />
                    ) : (
                      <span className="contact-value">{displayData.work_phone || '—'}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="profile-column profile-column--right">
              {/* Плашка Личные данные */}
              <div className="profile-section">
                <h3 className="profile-section__title">Личные данные</h3>
                <div className="profile-section__content">
                  <div className="field-row">
                    <span className="field-label">Навыки:</span>
                    <span className="field-value">{Array.isArray(displayData.skills) ? displayData.skills.join(', ') : displayData.skills || '—'}</span>
                  </div>
                  <div className="field-row">
                    <span className="field-label">Грейд:</span>
                    <span className="field-value">{displayData.grade || '—'}</span>
                  </div>
                  <div className="field-row field-row--bio">
                    <span className="field-label">Биография:</span>
                    {editing ? (
                      <ProfileField
                        value={displayData.bio}
                        editable={true}
                        editing={editing}
                        onChange={handleFieldChange}
                        type="textarea"
                        fieldName="bio"
                        hideLabel={true}
                      />
                    ) : (
                      <span className="field-value">{displayData.bio || '—'}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Плашка Локация и график */}
              <div className="profile-section">
                <h3 className="profile-section__title">Локация и график</h3>
                <div className="profile-section__content">
                  <div className="field-row">
                    <span className="field-label">Город:</span>
                    {editing ? (
                      <ProfileField
                        value={displayData.work_city}
                        editable={true}
                        editing={editing}
                        onChange={handleFieldChange}
                        fieldName="work_city"
                        hideLabel={true}
                      />
                    ) : (
                      <span className="field-value">{displayData.work_city || '—'}</span>
                    )}
                  </div>
                  <div className="field-row">
                    <span className="field-label">Формат работы:</span>
                    {editing ? (
                      <ProfileField
                        value={workFormatOptions.find(opt => opt.value === displayData.work_format)?.label}
                        editable={true}
                        editing={editing}
                        onChange={handleFieldChange}
                        type="select"
                        options={workFormatOptions}
                        fieldName="work_format"
                        hideLabel={true}
                      />
                    ) : (
                      <span className="field-value">
                        {workFormatOptions.find(opt => opt.value === displayData.work_format)?.label || '—'}
                      </span>
                    )}
                  </div>
                  <div className="field-row">
                    <span className="field-label">Часовой пояс:</span>
                    {editing ? (
                      <ProfileField
                        value={displayData.time_zone}
                        editable={true}
                        editing={editing}
                        onChange={handleFieldChange}
                        fieldName="time_zone"
                        hideLabel={true}
                      />
                    ) : (
                      <span className="field-value">{displayData.time_zone || '—'}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Profile;
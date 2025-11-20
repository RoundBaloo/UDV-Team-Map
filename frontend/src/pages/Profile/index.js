import React from 'react';
import Header from '../../components/common/Header';
import ProfileHeader from '../../components/profile/ProfileHeader';
import ProfileContacts from '../../components/profile/ProfileContacts';
import ProfilePersonal from '../../components/profile/ProfilePersonal';
import ProfileLocation from '../../components/profile/ProfileLocation';
import { useProfile } from '../../hooks/useProfile';
import './Profile.css';

const Profile = () => {
  const {
    profile,
    editing,
    editedData,
    loading,
    saving,
    error,
    isOwnProfile,
    moderationStatus,
    uploadingAvatar,
    handleEdit,
    handleCancel,
    handleSave,
    handleFieldChange,
    handleAvatarUploadStart,
    handleAvatarUploadSuccess,
    handleAvatarUploadError,
    getAvatarModerationStatus,
  } = useProfile();

  const handleAvatarChange = async (file, moderationItem) => {
    console.log('Avatar changed:', file, moderationItem);
  };

  if (loading) {
    return <LoadingState />;
  }

  if (!profile) {
    return <ErrorState error={error || 'Профиль не найден'} />;
  }

  const displayData = editing ? editedData : profile;

  return (
    <div className="profile-page">
      <Header />
      
      <main className="profile-main">
        <div className="container">
          <ErrorAlert error={error} />

          <div className="profile-layout">
            <div className="profile-column profile-column--left">
              <ProfileHeader
                profile={displayData}
                editing={editing}
                isOwnProfile={isOwnProfile}
                saving={saving}
                uploadingAvatar={uploadingAvatar}
                moderationStatus={moderationStatus}
                avatarModerationStatus={getAvatarModerationStatus()}
                currentAvatar={displayData.photo?.public_url}
                onEdit={handleEdit}
                onSave={handleSave}
                onCancel={handleCancel}
                onAvatarChange={handleAvatarChange}
                onAvatarUploadStart={handleAvatarUploadStart}
                onAvatarUploadSuccess={handleAvatarUploadSuccess}
                onAvatarUploadError={handleAvatarUploadError}
              />

              <ProfileContacts
                profile={displayData}
                editing={editing}
                onFieldChange={handleFieldChange}
              />
            </div>

            <div className="profile-column profile-column--right">
              <ProfilePersonal
                profile={displayData}
                editing={editing}
                onFieldChange={handleFieldChange}
              />

              <ProfileLocation
                profile={displayData}
                editing={editing}
                onFieldChange={handleFieldChange}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

const LoadingState = () => (
  <div className="profile-page">
    <Header />
    <main className="profile-main">
      <div className="container">
        <div className="loading-placeholder">Загрузка профиля...</div>
      </div>
    </main>
  </div>
);

const ErrorState = ({ error }) => (
  <div className="profile-page">
    <Header />
    <main className="profile-main">
      <div className="container">
        <div className="error-placeholder">{error}</div>
      </div>
    </main>
  </div>
);

const ErrorAlert = ({ error }) => {
  if (!error) return null;

  return (
    <div className={`alert ${error.includes('успешно') ? 'alert-success' : 'alert-error'}`}>
      {error}
    </div>
  );
};

export default Profile;
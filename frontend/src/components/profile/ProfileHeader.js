import React from 'react';
import AvatarUpload from './AvatarUpload';
import ProfileActions from './ProfileActions';

const ProfileHeader = ({
  profile,
  editing,
  isOwnProfile,
  saving,
  uploadingAvatar,
  moderationStatus,
  avatarModerationStatus,
  currentAvatar,
  onEdit,
  onSave,
  onCancel,
  onAvatarChange,
  onAvatarUploadStart,
  onAvatarUploadSuccess,
  onAvatarUploadError,
}) => {
  return (
    <div className="profile-card">
      <div className="profile-avatar-section">
        <AvatarUpload
          currentAvatar={currentAvatar}
          onAvatarChange={onAvatarChange}
          onUploadStart={onAvatarUploadStart}
          onUploadSuccess={onAvatarUploadSuccess}
          onUploadError={onAvatarUploadError}
          disabled={!editing || uploadingAvatar}
          moderationStatus={avatarModerationStatus}
        />
        
        <div className="profile-name-section">
          <div className="profile-full-name">
            <div className="last-name">{profile.last_name}</div>
            <div className="first-name">{profile.first_name}</div>
            <div className="middle-name">{profile.middle_name}</div>
          </div>
        </div>

        {isOwnProfile && moderationStatus?.has_request && moderationStatus.last?.status !== 'approved' && (
          <ModerationInfo moderationStatus={moderationStatus} />
        )} 
      </div>

      <ProfileMainInfo profile={profile} />
      
      <ProfileActions
        isEditing={editing}
        onEdit={onEdit}
        onSave={onSave}
        onCancel={onCancel}
        isOwnProfile={isOwnProfile}
        loading={saving || uploadingAvatar}
      />
    </div>
  );
};

const ModerationInfo = ({ moderationStatus }) => {
  if (moderationStatus.last?.status === 'pending') {
    return (
      <div className="moderation-info">
        <div className="moderation-status">
          Статус модерации: <strong>На рассмотрении</strong>
        </div>
      </div>
    );
  }

  if (moderationStatus.last?.status === 'rejected') {
    return (
      <div className="moderation-info">
        <div className="moderation-reason">
          <strong>Фото отклонено:</strong> {moderationStatus.last.reject_reason}
        </div>
      </div>
    );
  }

  return null;
};

const ProfileMainInfo = ({ profile }) => (
  <div className="profile-main-info">
    <div className="profile-info-row">
      <span className="profile-info-label">Должность:</span>
      <span className="profile-info-value">{profile.title}</span>
    </div>
    <div className="profile-info-row">
      <span className="profile-info-label">Юр. лицо:</span>
      <span className="profile-info-value">{profile.legal_entity}</span>
    </div>
    <div className="profile-info-row">
      <span className="profile-info-label">Отдел/группа:</span>
      <span className="profile-info-value">{profile.org_unit?.name}</span>
    </div>
  </div>
);

export default ProfileHeader;
import React from 'react';
import './ProfileActions.css';

const ProfileActions = ({ 
  isEditing, 
  onEdit, 
  onSave, 
  onCancel, 
  isOwnProfile = false,
  loading = false,
}) => {
  return (
    <div className="profile-actions">
      {!isEditing ? (
        <>
          {isOwnProfile && (
            <button 
              className="btn btn-primary profile-actions__btn"
              onClick={onEdit}
            >
              Редактировать профиль
            </button>
          )}
        </>
      ) : (
        <div className="profile-actions__edit-buttons">
          <button 
            className="btn btn-primary profile-actions__btn"
            onClick={onSave}
            disabled={loading}
          >
            {loading ? 'Сохранение...' : 'Сохранить'}
          </button>
          <button 
            className="btn btn-secondary profile-actions__btn"
            onClick={onCancel}
            disabled={loading}
          >
            Отмена
          </button>
        </div>
      )}
    </div>
  );
};

export default ProfileActions;
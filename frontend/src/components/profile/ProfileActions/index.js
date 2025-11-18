import React from 'react';
import './ProfileActions.css';

const BUTTON_TEXTS = {
  edit: 'Редактировать профиль',
  save: 'Сохранить',
  saving: 'Сохранение...',
  cancel: 'Отмена',
};

const ProfileActions = ({
  isEditing,
  onEdit,
  onSave,
  onCancel,
  isOwnProfile = false,
  loading = false,
}) => {
  if (!isOwnProfile) {
    return null;
  }

  return (
    <div className="profile-actions">
      {isEditing ? (
        <EditActions
          onSave={onSave}
          onCancel={onCancel}
          loading={loading}
        />
      ) : (
        <ViewActions onEdit={onEdit} />
      )}
    </div>
  );
};

const EditActions = ({ onSave, onCancel, loading }) => {
  return (
    <div className="profile-actions__edit-buttons">
      <ActionButton
        variant="primary"
        onClick={onSave}
        disabled={loading}
        text={loading ? BUTTON_TEXTS.saving : BUTTON_TEXTS.save}
      />
      <ActionButton
        variant="secondary"
        onClick={onCancel}
        disabled={loading}
        text={BUTTON_TEXTS.cancel}
      />
    </div>
  );
};

const ViewActions = ({ onEdit }) => {
  return (
    <ActionButton
      variant="primary"
      onClick={onEdit}
      text={BUTTON_TEXTS.edit}
    />
  );
};

const ActionButton = ({ variant, onClick, disabled, text }) => {
  return (
    <button
      className={`btn btn-${variant} profile-actions__btn`}
      onClick={onClick}
      disabled={disabled}
    >
      {text}
    </button>
  );
};

export default ProfileActions;
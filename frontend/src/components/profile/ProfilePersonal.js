import React from 'react';
import ProfileField from './ProfileField';

const ProfilePersonal = ({ profile, editing, onFieldChange }) => {
  return (
    <div className="profile-section">
      <h3 className="profile-section__title">Личные данные</h3>
      <div className="profile-section__content">
        <FieldRow
          label="Навыки:"
          value={Array.isArray(profile.skills) ? profile.skills.join(', ') : profile.skills}
        />
        <FieldRow
          label="Грейд:"
          value={profile.grade}
        />
        <BioField
          value={profile.bio}
          editing={editing}
          onFieldChange={onFieldChange}
        />
      </div>
    </div>
  );
};

const FieldRow = ({ label, value }) => (
  <div className="field-row">
    <span className="field-label">{label}</span>
    <span className="field-value">{value || '—'}</span>
  </div>
);

const BioField = ({ value, editing, onFieldChange }) => {
  if (editing) {
    return (
      <div className="field-row field-row--bio">
        <span className="field-label">Биография:</span>
        <ProfileField
          value={value}
          editable={true}
          editing={editing}
          onChange={onFieldChange}
          type="textarea"
          fieldName="bio"
          hideLabel={true}
        />
      </div>
    );
  }

  return (
    <div className="field-row field-row--bio">
      <span className="field-label">Биография:</span>
      <span className="field-value">{value || '—'}</span>
    </div>
  );
};

export default ProfilePersonal;
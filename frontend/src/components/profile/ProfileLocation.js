import React from 'react';
import ProfileField from './ProfileField';

const WORK_FORMAT_OPTIONS = [
  { value: 'office', label: 'Офис' },
  { value: 'hybrid', label: 'Гибридный' },
  { value: 'remote', label: 'Удаленный' },
];

const ProfileLocation = ({ profile, editing, onFieldChange }) => {
  const getWorkFormatLabel = () => {
    const option = WORK_FORMAT_OPTIONS.find(opt => opt.value === profile.work_format);
    return option?.label || '—';
  };

  return (
    <div className="profile-section">
      <h3 className="profile-section__title">Локация и график</h3>
      <div className="profile-section__content">
        <FieldRow
          label="Город:"
          value={profile.work_city}
          editing={editing}
          fieldName="work_city"
          onFieldChange={onFieldChange}
        />
        <WorkFormatField
          value={getWorkFormatLabel()}
          editing={editing}
          onFieldChange={onFieldChange}
        />
        <FieldRow
          label="Часовой пояс:"
          value={profile.time_zone}
          editing={editing}
          fieldName="time_zone"
          onFieldChange={onFieldChange}
        />
      </div>
    </div>
  );
};

const FieldRow = ({ label, value, editing, fieldName, onFieldChange }) => {
  if (editing && fieldName) {
    return (
      <div className="field-row">
        <span className="field-label">{label}</span>
        <ProfileField
          value={value}
          editable={true}
          editing={editing}
          onChange={onFieldChange}
          fieldName={fieldName}
          hideLabel={true}
        />
      </div>
    );
  }

  return (
    <div className="field-row">
      <span className="field-label">{label}</span>
      <span className="field-value">{value || '—'}</span>
    </div>
  );
};

const WorkFormatField = ({ value, editing, onFieldChange }) => {
  if (editing) {
    return (
      <div className="field-row">
        <span className="field-label">Формат работы:</span>
        <ProfileField
          value={value}
          editable={true}
          editing={editing}
          onChange={onFieldChange}
          type="select"
          options={WORK_FORMAT_OPTIONS}
          fieldName="work_format"
          hideLabel={true}
        />
      </div>
    );
  }

  return (
    <div className="field-row">
      <span className="field-label">Формат работы:</span>
      <span className="field-value">{value}</span>
    </div>
  );
};

export default ProfileLocation;
import React from 'react';
import './ProfileField.css';

const ProfileField = ({ 
  label, 
  value, 
  editable = false, 
  editing = false, 
  onChange,
  type = 'text',
  options,
  fieldName,
}) => {
  const isReadOnlyFromAD = fieldName && [
    'first_name', 'last_name', 'email', 'title', 'department', 'manager', 'status',
  ].includes(fieldName);

  const renderField = () => {
    if (editing && editable) {
      if (type === 'select' && options) {
        return (
          <select
            className="profile-field__input"
            value={value || ''}
            onChange={(e) => onChange(fieldName, e.target.value)}
          >
            {options.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
      }
      
      if (type === 'textarea') {
        return (
          <textarea
            className="profile-field__input profile-field__textarea"
            value={value || ''}
            onChange={(e) => onChange(fieldName, e.target.value)}
            rows={3}
          />
        );
      }

      return (
        <input
          type={type}
          className="profile-field__input"
          value={value || ''}
          onChange={(e) => onChange(fieldName, e.target.value)}
        />
      );
    }

    return (
      <div className="profile-field__value">
        {value || <span className="profile-field__empty">Не указано</span>}
        {isReadOnlyFromAD && (
          <div className="profile-field__hint">
            Данные синхронизируются из AD
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="profile-field">
      <label className="profile-field__label">
        {label}
        {isReadOnlyFromAD && ' *'}
      </label>
      {renderField()}
    </div>
  );
};

export default ProfileField;
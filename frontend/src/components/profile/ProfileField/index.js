import React from 'react';
import './ProfileField.css';

const READ_ONLY_FIELDS = [
  'first_name',
  'last_name', 
  'email',
  'title',
  'department',
  'manager',
  'status',
];

const DEFAULT_TEXTS = {
  empty: 'Не указано',
  adHint: 'Данные синхронизируются из AD',
};

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
  const isReadOnlyFromAD = fieldName && READ_ONLY_FIELDS.includes(fieldName);
  const shouldRenderInput = editing && editable;

  return (
    <div className="profile-field">
      <FieldLabel 
        label={label}
        isReadOnlyFromAD={isReadOnlyFromAD}
      />
      
      {shouldRenderInput ? (
        <FieldInput
          type={type}
          value={value}
          fieldName={fieldName}
          onChange={onChange}
          options={options}
        />
      ) : (
        <FieldDisplay
          value={value}
          isReadOnlyFromAD={isReadOnlyFromAD}
        />
      )}
    </div>
  );
};

const FieldLabel = ({ label, isReadOnlyFromAD }) => (
  <label className="profile-field__label">
    {label}
    {isReadOnlyFromAD && ' *'}
  </label>
);

const FieldInput = ({ type, value, fieldName, onChange, options }) => {
  const handleChange = newValue => {
    onChange(fieldName, newValue);
  };

  if (type === 'select' && options) {
    return (
      <SelectInput
        value={value}
        options={options}
        onChange={handleChange}
      />
    );
  }

  if (type === 'textarea') {
    return (
      <TextareaInput
        value={value}
        onChange={handleChange}
      />
    );
  }

  return (
    <TextInput
      type={type}
      value={value}
      onChange={handleChange}
    />
  );
};

const SelectInput = ({ value, options, onChange }) => (
  <select
    className="profile-field__input"
    value={value || ''}
    onChange={e => onChange(e.target.value)}
  >
    {options.map(option => (
      <option key={option.value} value={option.value}>
        {option.label}
      </option>
    ))}
  </select>
);

const TextareaInput = ({ value, onChange }) => (
  <textarea
    className="profile-field__input profile-field__textarea"
    value={value || ''}
    onChange={e => onChange(e.target.value)}
    rows={3}
  />
);

const TextInput = ({ type, value, onChange }) => (
  <input
    type={type}
    className="profile-field__input"
    value={value || ''}
    onChange={e => onChange(e.target.value)}
  />
);

const FieldDisplay = ({ value, isReadOnlyFromAD }) => (
  <div className="profile-field__value">
    {value || <span className="profile-field__empty">{DEFAULT_TEXTS.empty}</span>}
    
    {isReadOnlyFromAD && (
      <div className="profile-field__hint">
        {DEFAULT_TEXTS.adHint}
      </div>
    )}
  </div>
);

export default ProfileField;
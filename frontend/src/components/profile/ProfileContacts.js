import React from 'react';
import ProfileField from './ProfileField';

const ProfileContacts = ({ profile, editing, onFieldChange }) => {
  return (
    <div className="profile-section profile-section--contacts">
      <h3 className="profile-section__title">Контакты</h3>
      <div className="profile-section__content">
        <ContactRow
          label="Mattermost:"
          value={profile.mattermost_handle}
          editing={editing}
          fieldName="mattermost_handle"
          onFieldChange={onFieldChange}
        />
        <ContactRow
          label="Email:"
          value={profile.email}
          editing={false}
        />
        <ContactRow
          label="Telegram:"
          value={profile.telegram}
          editing={false}
        />
        <ContactRow
          label="Телефон:"
          value={profile.work_phone}
          editing={editing}
          fieldName="work_phone"
          onFieldChange={onFieldChange}
        />
      </div>
    </div>
  );
};

const ContactRow = ({ label, value, editing, fieldName, onFieldChange }) => {
  if (editing && fieldName) {
    return (
      <div className="contact-row">
        <span className="contact-label">{label}</span>
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
    <div className="contact-row">
      <span className="contact-label">{label}</span>
      <span className="contact-value">{value || '—'}</span>
    </div>
  );
};

export default ProfileContacts;
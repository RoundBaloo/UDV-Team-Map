import React from 'react';

const MemberCard = ({ member, onClick }) => {
  const getInitials = employee => {
    if (!employee) return '??';
    return `${employee.first_name?.[0] || ''}${employee.last_name?.[0] || ''}`;
  };

  const getFullName = employee => {
    if (!employee) return 'Неизвестный сотрудник';
    return `${employee.first_name || ''} ${employee.last_name || ''}`.trim();
  };

  return (
    <div 
      className="member-card clickable-card"
      onClick={onClick}
    >
      <div className="member-avatar">
        {member.photo ? (
          <img src={member.photo} alt={getFullName(member)} />
        ) : (
          <div className="avatar-placeholder">
            {getInitials(member)}
          </div>
        )}
      </div>
      <div className="member-info">
        <div className="member-name">
          {getFullName(member)}
        </div>
        <div className="member-title">{member.title || 'Должность не указана'}</div>
        <div className="member-contact">
          {member.email || 'Email не указан'}
        </div>
      </div>
    </div>
  );
};

export default MemberCard;
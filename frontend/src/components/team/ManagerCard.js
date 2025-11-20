import React from 'react';

const ManagerCard = ({ manager, onClick }) => {
  const getInitials = employee => {
    if (!employee) return '??';
    return `${employee.first_name?.[0] || ''}${employee.last_name?.[0] || ''}`;
  };

  const getFullName = employee => {
    if (!employee) return 'Неизвестный сотрудник';
    return `${employee.first_name || ''} ${employee.last_name || ''}`.trim();
  };

  return (
    <div className="team-section">
      <h2>Руководитель</h2>
      <div 
        className="manager-card clickable-card"
        onClick={onClick}
      >
        <div className="manager-avatar">
          {manager.photo ? (
            <img src={manager.photo} alt={getFullName(manager)} />
          ) : (
            <div className="avatar-placeholder">
              {getInitials(manager)}
            </div>
          )}
        </div>
        <div className="manager-info">
          <div className="manager-name">
            {getFullName(manager)}
          </div>
          <div className="manager-title">{manager.title || 'Должность не указана'}</div>
          <div className="manager-contact">
            {manager.email || 'Email не указан'} • {manager.work_phone || 'Телефон не указан'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManagerCard;
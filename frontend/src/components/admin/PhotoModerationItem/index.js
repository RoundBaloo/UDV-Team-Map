import './PhotoModerationItem.css';

const PhotoModerationItem = ({ 
  item, 
  onApprove, 
  onReject,
  loading = false,
}) => {
  const {
    photo_moderation_id,
    id,
    employee_id,
    employee,
    photo,
  } = item;

  const moderationId = photo_moderation_id || id;
  const employeeName = employee 
    ? `${employee.first_name} ${employee.last_name}`
    : `Сотрудник #${employee_id}`;
  const photoUrl = photo?.public_url;

  const handleRejectClick = () => {
    onReject?.(moderationId, 'Не соотв. требованиям');
  };

  const handleApproveClick = () => {
    onApprove?.(moderationId);
  };

  const handleImageError = (e) => {
    e.target.style.display = 'none';
    const placeholder = e.target.nextElementSibling;
    if (placeholder) {
      placeholder.style.display = 'flex';
    }
  };

  return (
    <div className="photo-moderation-item">
      <div className="photo-moderation-item__photo">
        {photoUrl ? (
          <img 
            src={photoUrl} 
            alt={`Фото ${employeeName}`}
            className="photo-moderation-item__image"
            onError={handleImageError}
          />
        ) : null}
        <div className="photo-moderation-item__placeholder">
          📷
        </div>
      </div>

      <div className="photo-moderation-item__name">
        {employeeName}
      </div>

      <div className="photo-moderation-item__actions">
        <button
          className="photo-moderation-item__btn photo-moderation-item__btn--approve"
          onClick={handleApproveClick}
          disabled={loading}
        >
          Одобрить
        </button>
        <button
          className="photo-moderation-item__btn photo-moderation-item__btn--reject"
          onClick={handleRejectClick}
          disabled={loading}
        >
          Отклонить
        </button>
      </div>
    </div>
  );
};

export default PhotoModerationItem;
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

  // Получаем ID модерации (новый или старый)
  const getModerationId = () => {
    return photo_moderation_id || id;
  };

  // Форматируем имя сотрудника
  const getEmployeeName = () => {
    if (employee) {
      return `${employee.first_name} ${employee.last_name}`;
    }
    return `Сотрудник #${employee_id}`;
  };

  // Получаем URL фото
  const getPhotoUrl = () => {
    return photo?.public_url;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const handleRejectClick = () => {
    // В коде, т.к. сказали, не нужно, бек не переписывали еще
    const rejectReason = 'Не соотв. требованиям';
    onReject?.(getModerationId(), rejectReason);
  };

  const handleApproveClick = () => {
    onApprove?.(getModerationId());
  };

  return (
    <div className="photo-moderation-item">
      <div className="photo-moderation-item__photo">
        {getPhotoUrl() ? (
          <img 
            src={getPhotoUrl()} 
            alt={`Фото ${getEmployeeName()}`}
            className="photo-moderation-item__image"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
        ) : null}
        <div className="photo-moderation-item__placeholder">
          📷
        </div>
      </div>

      <div className="photo-moderation-item__name">
        {getEmployeeName()}
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
import React, { useState, useEffect } from 'react';
import Header from '../../components/common/Header';
import Breadcrumbs from '../../components/common/Breadcrumbs';
import PhotoModerationItem from '../../components/admin/PhotoModerationItem';
import { photoModerationApi } from '../../services/api/photoModeration';
import './PhotoModeration.css';

const PhotoModeration = () => {
  const [pendingPhotos, setPendingPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 50,
    offset: 0,
  });

  useEffect(() => {
    loadPendingPhotos();
  }, []);

  const loadPendingPhotos = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await photoModerationApi.getPendingPhotos({
        limit: pagination.limit,
        offset: pagination.offset,
      });
      
      setPendingPhotos(response.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
      }));
    } catch (err) {
      console.error('Error loading pending photos:', err);
      setError('Не удалось загрузить фотографии на модерацию');
      
      // Если API недоступно, показываем пустой список
      setPendingPhotos([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (moderationId) => {
    setProcessingId(moderationId);
    setError(null);

    try {
      await photoModerationApi.approvePhoto(moderationId);
      
      // Удаляем одобренную фото из списка
      setPendingPhotos(prev => prev.filter(photo => 
        photo.photo_moderation_id !== moderationId 
      ));
      
      // Обновляем пагинацию
      setPagination(prev => ({
        ...prev,
        total: prev.total - 1,
      }));
      
      console.log('Photo approved:', moderationId);
    } catch (err) {
      console.error('Error approving photo:', err);
      setError('Ошибка при одобрении фото');
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (moderationId, reason) => {
    setProcessingId(moderationId);
    setError(null);

    try {
      await photoModerationApi.rejectPhoto(moderationId, reason);
      
      // Удаляем отклоненную фото из списка
      setPendingPhotos(prev => prev.filter(photo => 
        photo.photo_moderation_id !== moderationId 
      ));
      
      // Обновляем пагинацию
      setPagination(prev => ({
        ...prev,
        total: prev.total - 1,
      }));
      
      console.log('Photo rejected:', moderationId, reason);
    } catch (err) {
      console.error('Error rejecting photo:', err);
      setError('Ошибка при отклонении фото');
    } finally {
      setProcessingId(null);
    }
  };

  const handleRetry = () => {
    loadPendingPhotos();
  };

  if (loading) {
    return (
      <div className="photo-moderation-page">
        <Header />
        {/* <Breadcrumbs /> */}
        <main className="photo-moderation-main">
          <div className="container">
            <div className="loading-placeholder">Загрузка фотографий на модерацию...</div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="photo-moderation-page">
      <Header />
      {/* <Breadcrumbs /> */}
      
      <main className="photo-moderation-main">
        <div className="container">
          <div className="photo-moderation-header">
            <h1>Модерация фотографий</h1>
            {pendingPhotos.length > 0 && (
              <div className="photo-moderation-stats">
                Ожидают модерации: {pendingPhotos.length}
              </div>
            )}
          </div>

          {error && (
            <div className="alert alert-error">
              {error}
              <button 
                className="btn btn-secondary btn-sm"
                onClick={handleRetry}
                style={{ marginLeft: '10px' }}
              >
                Повторить
              </button>
            </div>
          )}

          <div className="photo-moderation-content">
            {pendingPhotos.length > 0 ? (
              <div className="photo-moderation-grid">
                {pendingPhotos.map(photo => (
                  <PhotoModerationItem
                    key={photo.photo_moderation_id || photo.id} 
                    item={photo}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    loading={processingId === (photo.photo_moderation_id || photo.id)} 
                  />
                ))}
              </div>
            ) : (
              <div className="photo-moderation-empty">
                <div className="empty-state">
                  <div className="empty-state__icon">📷</div>
                  <h3>Нет фотографий для модерации</h3>
                  <p>Все фотографии обработаны или произошла ошибка загрузки</p>
                  {error && (
                    <button 
                      className="btn btn-primary"
                      onClick={handleRetry}
                    >
                      Попробовать снова
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Пагинация */}
          {pagination.total > pagination.limit && (
            <div className="photo-moderation-pagination">
              <button 
                className="btn btn-secondary"
                disabled={pagination.offset === 0}
                onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset - prev.limit }))}
              >
                Назад
              </button>
              <span>
                Страница {Math.floor(pagination.offset / pagination.limit) + 1} из {Math.ceil(pagination.total / pagination.limit)}
              </span>
              <button 
                className="btn btn-secondary"
                disabled={pagination.offset + pagination.limit >= pagination.total}
                onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
              >
                Вперед
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default PhotoModeration;
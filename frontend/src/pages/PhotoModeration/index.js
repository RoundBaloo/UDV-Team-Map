import React, { useState, useEffect } from 'react';
import Header from '../../components/common/Header';
import PhotoModerationItem from '../../components/admin/PhotoModerationItem';
import { photoModerationApi } from '../../services/api/photoModeration';
import './PhotoModeration.css';

const PAGINATION_CONFIG = {
  LIMIT: 50,
};

const PhotoModeration = () => {
  const [state, setState] = useState({
    pendingPhotos: [],
    loading: true,
    processingId: null,
    error: null,
    pagination: {
      total: 0,
      limit: PAGINATION_CONFIG.LIMIT,
      offset: 0,
    },
  });

  useEffect(() => {
    loadPendingPhotos();
  }, [state.pagination.offset]);

  const loadPendingPhotos = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const response = await photoModerationApi.getPendingPhotos({
        limit: state.pagination.limit,
        offset: state.pagination.offset,
      });
      
      setState(prev => ({
        ...prev,
        pendingPhotos: response.items || [],
        pagination: { ...prev.pagination, total: response.total || 0 },
      }));
    } catch (err) {
      console.error('Error loading pending photos:', err);
      setState(prev => ({
        ...prev,
        error: 'Не удалось загрузить фотографии на модерацию',
        pendingPhotos: [],
      }));
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  const handleModeration = async (moderationId, action, reason) => {
    setState(prev => ({ ...prev, processingId: moderationId, error: null }));

    try {
      if (action === 'approve') {
        await photoModerationApi.approvePhoto(moderationId);
      } else {
        await photoModerationApi.rejectPhoto(moderationId, reason);
      }
      
      setState(prev => ({
        ...prev,
        pendingPhotos: prev.pendingPhotos.filter(photo => 
          photo.photo_moderation_id !== moderationId 
        ),
        pagination: { ...prev.pagination, total: prev.pagination.total - 1 },
      }));
      
      console.log(`Photo ${action}ed:`, moderationId, reason);
    } catch (err) {
      console.error(`Error ${action}ing photo:`, err);
      setState(prev => ({ 
        ...prev, 
        error: `Ошибка при ${action === 'approve' ? 'одобрении' : 'отклонении'} фото`,
      }));
    } finally {
      setState(prev => ({ ...prev, processingId: null }));
    }
  };

  const handleApprove = moderationId => {
    handleModeration(moderationId, 'approve');
  };

  const handleReject = (moderationId, reason) => {
    handleModeration(moderationId, 'reject', reason);
  };

  const handleRetry = () => {
    loadPendingPhotos();
  };

  const handlePagination = direction => {
    setState(prev => ({
      ...prev,
      pagination: {
        ...prev.pagination,
        offset: direction === 'next' 
          ? prev.pagination.offset + prev.pagination.limit
          : prev.pagination.offset - prev.pagination.limit,
      },
    }));
  };

  if (state.loading) {
    return <LoadingState />;
  }

  return (
    <div className="photo-moderation-page">
      <Header />
      
      <main className="photo-moderation-main">
        <div className="container">
          <PhotoModerationHeader 
            photosCount={state.pendingPhotos.length}
          />

          {state.error && (
            <ErrorAlert 
              error={state.error}
              onRetry={handleRetry}
            />
          )}

          <PhotoModerationContent
            pendingPhotos={state.pendingPhotos}
            processingId={state.processingId}
            error={state.error}
            onApprove={handleApprove}
            onReject={handleReject}
            onRetry={handleRetry}
          />

          <Pagination
            pagination={state.pagination}
            onPagination={handlePagination}
          />
        </div>
      </main>
    </div>
  );
};

const LoadingState = () => (
  <div className="photo-moderation-page">
    <Header />
    <main className="photo-moderation-main">
      <div className="container">
        <div className="loading-placeholder">
          Загрузка фотографий на модерацию...
        </div>
      </div>
    </main>
  </div>
);

const PhotoModerationHeader = ({ photosCount }) => (
  <div className="photo-moderation-header">
    <h1>Модерация фотографий</h1>
    {photosCount > 0 && (
      <div className="photo-moderation-stats">
        Ожидают модерации: {photosCount}
      </div>
    )}
  </div>
);

const ErrorAlert = ({ error, onRetry }) => (
  <div className="alert alert-error">
    {error}
    <button 
      className="btn btn-secondary btn-sm"
      onClick={onRetry}
      style={{ marginLeft: '10px' }}
    >
      Повторить
    </button>
  </div>
);

const PhotoModerationContent = ({ 
  pendingPhotos, 
  processingId, 
  error, 
  onApprove, 
  onReject, 
  onRetry,
}) => {
  if (pendingPhotos.length > 0) {
    return (
      <div className="photo-moderation-grid">
        {pendingPhotos.map(photo => (
          <PhotoModerationItem
            key={photo.photo_moderation_id || photo.id}
            item={photo}
            onApprove={onApprove}
            onReject={onReject}
            loading={processingId === (photo.photo_moderation_id || photo.id)}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="photo-moderation-empty">
      <div className="empty-state">
        <div className="empty-state__icon">📷</div>
        <h3>Нет фотографий для модерации</h3>
        <p>Все фотографии обработаны или произошла ошибка загрузки</p>
        {error && (
          <button 
            className="btn btn-primary"
            onClick={onRetry}
          >
            Попробовать снова
          </button>
        )}
      </div>
    </div>
  );
};

const Pagination = ({ pagination, onPagination }) => {
  if (pagination.total <= pagination.limit) {
    return null;
  }

  const currentPage = Math.floor(pagination.offset / pagination.limit) + 1;
  const totalPages = Math.ceil(pagination.total / pagination.limit);

  return (
    <div className="photo-moderation-pagination">
      <button 
        className="btn btn-secondary"
        disabled={pagination.offset === 0}
        onClick={() => onPagination('prev')}
      >
        Назад
      </button>
      <span>
        Страница {currentPage} из {totalPages}
      </span>
      <button 
        className="btn btn-secondary"
        disabled={pagination.offset + pagination.limit >= pagination.total}
        onClick={() => onPagination('next')}
      >
        Вперед
      </button>
    </div>
  );
};

export default PhotoModeration;
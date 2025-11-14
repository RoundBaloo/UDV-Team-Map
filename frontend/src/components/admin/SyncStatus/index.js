import React from 'react';
import './SyncStatus.css';

const SyncStatus = ({ 
  lastSync, 
  status, 
  errors = 0,
  onManualSync,
  loading = false,
}) => {
  const getStatusInfo = () => {
    switch (status) {
      case 'success':
        return { class: 'sync-status--success', text: 'Успешно' };
      case 'error':
        return { class: 'sync-status--error', text: 'Ошибка' };
      case 'syncing':
        return { class: 'sync-status--syncing', text: 'Синхронизация...' };
      default:
        return { class: 'sync-status--idle', text: 'Не запускалась' };
    }
  };

  const statusInfo = getStatusInfo();

  const formatDateTime = (dateString) => {
    if (!dateString) return 'Никогда';
    
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className={`sync-status ${statusInfo.class}`}>
      <div className="sync-status__header">
        <h3 className="sync-status__title">Синхронизация с AD</h3>
        <button
          className="btn btn-primary btn-sm"
          onClick={onManualSync}
          disabled={loading || status === 'syncing'}
        >
          {status === 'syncing' ? 'Синхронизация...' : 'Запустить вручную'}
        </button>
      </div>

      <div className="sync-status__content">
        <div className="sync-status__item">
          <span className="sync-status__label">Статус:</span>
          <span className="sync-status__value">
            <span className="sync-status__indicator"></span>
            {statusInfo.text}
          </span>
        </div>

        <div className="sync-status__item">
          <span className="sync-status__label">Последняя синхронизация:</span>
          <span className="sync-status__value">{formatDateTime(lastSync)}</span>
        </div>

        {errors > 0 && (
          <div className="sync-status__item">
            <span className="sync-status__label">Ошибки:</span>
            <span className="sync-status__value sync-status__errors">{errors} конфликтов</span>
          </div>
        )}

        <div className="sync-status__item">
          <span className="sync-status__label">Расписание:</span>
          <span className="sync-status__value">Каждые 24 часа</span>
        </div>
      </div>
    </div>
  );
};

export default SyncStatus;
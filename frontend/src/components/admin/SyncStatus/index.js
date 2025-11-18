import React from 'react';
import { formatDateTime } from '../../utils/helpers';
import './SyncStatus.css';

const STATUS_CONFIG = {
  success: { class: 'sync-status--success', text: 'Успешно' },
  error: { class: 'sync-status--error', text: 'Ошибка' },
  syncing: { class: 'sync-status--syncing', text: 'Синхронизация...' },
  idle: { class: 'sync-status--idle', text: 'Не запускалась' },
};

const SyncStatus = ({ 
  lastSync, 
  status, 
  errors = 0,
  onManualSync,
  loading = false,
  schedule = 'Каждые 24 часа',
}) => {
  const statusInfo = STATUS_CONFIG[status] || STATUS_CONFIG.idle;
  const isSyncing = status === 'syncing';
  const buttonText = isSyncing ? 'Синхронизация...' : 'Запустить вручную';

  return (
    <div className={`sync-status ${statusInfo.class}`}>
      <div className="sync-status__header">
        <h3 className="sync-status__title">Синхронизация с AD</h3>
        <button
          className="btn btn-primary btn-sm"
          onClick={onManualSync}
          disabled={loading || isSyncing}
        >
          {buttonText}
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
          <span className="sync-status__value">
            {formatDate(lastSync, true)}
          </span>
        </div>

        {errors > 0 && (
          <div className="sync-status__item">
            <span className="sync-status__label">Ошибки:</span>
            <span className="sync-status__value sync-status__errors">{errors} конфликтов</span>
          </div>
        )}

        <div className="sync-status__item">
          <span className="sync-status__label">Расписание:</span>
          <span className="sync-status__value">{schedule}</span>
        </div>
      </div>
    </div>
  );
};

export default SyncStatus;
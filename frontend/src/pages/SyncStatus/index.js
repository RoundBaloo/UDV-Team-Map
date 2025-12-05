import React, { useState, useEffect, useCallback } from 'react';
import Header from '../../components/common/Header';
import { syncApi } from '../../services/api/sync';
import Table, { useTableSort } from '../../components/common/Table';
import './SyncStatus.css';

const SyncStatus = () => {
  const [syncJobs, setSyncJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const { sortedData, handleSort, sortConfig } = useTableSort(syncJobs);

  const fetchSyncJobs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await syncApi.getJobs();
      setSyncJobs(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching sync jobs:', err);
      setError('Не удалось загрузить данные синхронизации');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchSyncJobs();
  }, [fetchSyncJobs]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchSyncJobs();
  };

  const handleRunSync = async () => {
    try {
      setRefreshing(true);
      await syncApi.runSync();
      fetchSyncJobs();
    } catch (err) {
      console.error('Error running sync:', err);
      setError('Не удалось запустить синхронизацию');
      setRefreshing(false);
    }
  };

  const columns = [
    {
      key: 'job_id',
      title: 'ID',
      sortable: true,
      width: '15%',
      render: (value) => <span className="sync-job-id">#{value}</span>,
    },
    {
      key: 'status',
      title: 'Статус',
      sortable: true,
      width: '25%',
      render: (value) => {
        const statusClasses = {
          completed: 'sync-status-completed',
          running: 'sync-status-running',
          failed: 'sync-status-failed',
          pending: 'sync-status-pending',
        };
        
        const statusLabels = {
          completed: 'Завершено',
          running: 'Выполняется',
          failed: 'Ошибка',
          pending: 'Ожидает',
        };
        
        const className = statusClasses[value] || 'sync-status-unknown';
        const label = statusLabels[value] || value;
        
        return <span className={`sync-status ${className}`}>{label}</span>;
      },
    },
    {
      key: 'finished_date',
      title: 'Дата окончания',
      sortable: true,
      width: '30%',
      render: (value, row) => {
        if (!value) {
          if (row.status === 'running') {
            return <span className="sync-in-progress">В процессе</span>;
          }
          return '-';
        }
        
        const date = new Date(value);
        return date.toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        });
      },
    },
    {
      key: 'summary',
      title: 'Есть ошибки',
      sortable: false,
      width: '30%',
      render: (value) => {
        if (!value) return '-';
        
        const { errors } = value;
        
        if (errors > 0) {
          return (
            <div className="sync-errors">
              <span className="sync-errors-badge">⚠️</span>
              <span>Есть проблемы ({errors})</span>
            </div>
          );
        }
        
        return <span>Нет ошибок</span>;
      },
    },
  ];

  if (loading && !refreshing) {
    return (
      <div className="sync-status-page">
        <Header />
        <main className="sync-status-main">
          <div className="container">
            <div className="sync-status-loading">
              <div className="sync-status-spinner" />
              <span>Загрузка данных...</span>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="sync-status-page">
      <Header />
      
      <main className="sync-status-main">
        <div className="container">
          <div className="sync-status-header">
            <h1>Синхронизация</h1>
            <div className="sync-actions">
              <button
                className="btn btn-secondary"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                {refreshing ? (
                  <>
                    <span className="refresh-spinner" />
                    Обновление...
                  </>
                ) : (
                  'Обновить'
                )}
              </button>
              <button
                className="btn btn-primary"
                onClick={handleRunSync}
                disabled={refreshing}
              >
                Запустить синхронизацию
              </button>
            </div>
          </div>

          {error && (
            <div className="sync-error-alert">
              <span className="sync-error-icon">⚠️</span>
              <span>{error}</span>
              <button
                className="sync-error-retry"
                onClick={fetchSyncJobs}
              >
                Повторить
              </button>
            </div>
          )}

          <div className="sync-table-container">
            <Table
              data={sortedData}
              columns={columns}
              loading={refreshing}
              selectable={false}
              sortConfig={sortConfig}
              onSort={handleSort}
              emptyMessage="Нет данных о синхронизации"
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default SyncStatus;
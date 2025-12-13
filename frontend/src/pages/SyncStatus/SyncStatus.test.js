import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SyncStatus from './index';

jest.mock('../../components/common/Header', () => () => <div data-testid="mock-header">Header</div>);

jest.mock('../../components/common/Table', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: ({ data = [], columns = [], emptyMessage }) => (
      <div data-testid="mock-table">
        {data.length > 0 ? (
          data.map((row) => (
            <div key={row.job_id} data-testid={`row-${row.job_id}`}>
              {columns.map((column) => {
                const value = column.render 
                  ? column.render(row[column.key], row)
                  : row[column.key];
                return (
                  <span key={column.key} data-testid={`row-${column.key}-${row.job_id}`}>
                    {value}
                  </span>
                );
              })}
            </div>
          ))
        ) : (
          <div data-testid="empty-message">{emptyMessage}</div>
        )}
      </div>
    ),
    useTableSort: (data) => ({
      sortedData: data,
      handleSort: jest.fn(),
      sortConfig: null,
    }),
  };
});

jest.mock('../../services/api/sync', () => ({
  syncApi: {
    getJobs: jest.fn(),
    runSync: jest.fn(),
  },
}));

const { syncApi } = require('../../services/api/sync');

describe('SyncStatus page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('показывает loading state', async () => {
    syncApi.getJobs.mockImplementation(() => new Promise(() => {})); 
    
    render(<SyncStatus />);
    expect(screen.getByText(/Загрузка данных/i)).toBeInTheDocument();
    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
  });

  test('рендерит таблицу с данными после загрузки', async () => {
    const jobs = [
      { job_id: 1, status: 'completed', finished_date: '2025-12-13T12:00:00Z', summary: { errors: 0 } },
      { job_id: 2, status: 'failed', finished_date: null, summary: { errors: 2 } },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      expect(screen.getByTestId('mock-table')).toBeInTheDocument();
      expect(screen.getByTestId('row-1')).toBeInTheDocument();
      expect(screen.getByTestId('row-2')).toBeInTheDocument();
    });
  });

  test('показывает сообщение об ошибке при API error', async () => {
    syncApi.getJobs.mockRejectedValue(new Error('API error'));
    render(<SyncStatus />);
    await waitFor(() => {
      expect(screen.getByText(/Не удалось загрузить данные синхронизации/i)).toBeInTheDocument();
    });
  });

  test('кнопка обновления вызывает fetchSyncJobs', async () => {
    const jobs = [{ job_id: 1 }];
    syncApi.getJobs.mockResolvedValue(jobs);
    render(<SyncStatus />);
    await waitFor(() => screen.getByTestId('mock-table'));

    fireEvent.click(screen.getByText(/Обновить/i));
    await waitFor(() => expect(screen.getByTestId('mock-table')).toBeInTheDocument());
  });

  test('кнопка запуска синхронизации вызывает runSync и обновляет таблицу', async () => {
    const jobsBefore = [{ job_id: 1, status: 'completed', finished_date: null, summary: null }];
    const jobsAfter = [{ job_id: 2, status: 'completed', finished_date: null, summary: null }];
    syncApi.getJobs.mockResolvedValueOnce(jobsBefore).mockResolvedValueOnce(jobsAfter);
    syncApi.runSync.mockResolvedValue({});

    render(<SyncStatus />);
    await waitFor(() => screen.getByTestId('row-1'));

    fireEvent.click(screen.getByText(/Запустить синхронизацию/i));
    await waitFor(() => screen.getByTestId('row-2'));
  });

  test('обрабатывает ошибку при запуске синхронизации', async () => {
    const jobs = [{ job_id: 1, status: 'completed' }];
    syncApi.getJobs.mockResolvedValue(jobs);
    syncApi.runSync.mockRejectedValue(new Error('Sync failed'));

    render(<SyncStatus />);
    await waitFor(() => screen.getByTestId('mock-table'));

    fireEvent.click(screen.getByText(/Запустить синхронизацию/i));
    
    await waitFor(() => {
      expect(screen.getByText(/Не удалось запустить синхронизацию/i)).toBeInTheDocument();
    });
  });

  test('рендерит колонку job_id с правильным форматом', async () => {
    const jobs = [
      { job_id: 123, status: 'completed', finished_date: '2025-12-13T12:00:00Z', summary: { errors: 0 } },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      const jobIdCell = screen.getByTestId('row-job_id-123');
      expect(jobIdCell).toBeInTheDocument();
      expect(jobIdCell).toHaveTextContent('#123');
    });
  });

  test('рендерит колонку status для всех статусов', async () => {
    const jobs = [
      { job_id: 1, status: 'completed', finished_date: '2025-12-13T12:00:00Z', summary: { errors: 0 } },
      { job_id: 2, status: 'running', finished_date: null, summary: null },
      { job_id: 3, status: 'failed', finished_date: '2025-12-13T12:00:00Z', summary: { errors: 1 } },
      { job_id: 4, status: 'pending', finished_date: null, summary: null },
      { job_id: 5, status: 'unknown_status', finished_date: null, summary: null },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      // Проверяем все статусы
      expect(screen.getByText('Завершено')).toBeInTheDocument();
      expect(screen.getByText('Выполняется')).toBeInTheDocument();
      expect(screen.getByText('Ошибка')).toBeInTheDocument();
      expect(screen.getByText('Ожидает')).toBeInTheDocument();
      expect(screen.getByText('unknown_status')).toBeInTheDocument();
    });
  });

  test('рендерит колонку finished_date с датой', async () => {
    const jobs = [
      { 
        job_id: 1, 
        status: 'completed', 
        finished_date: '2025-12-13T14:30:00Z', 
        summary: { errors: 0 } 
      },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      const dateCell = screen.getByTestId('row-finished_date-1');
      expect(dateCell).toBeInTheDocument();
      // Проверяем, что дата отформатирована (должна содержать числа)
      expect(dateCell.textContent).toMatch(/\d{2}/);
    });
  });

  test('рендерит колонку finished_date для running статуса', async () => {
    const jobs = [
      { 
        job_id: 1, 
        status: 'running', 
        finished_date: null, 
        summary: null 
      },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      const dateCell = screen.getByTestId('row-finished_date-1');
      expect(dateCell).toBeInTheDocument();
      expect(dateCell).toHaveTextContent('В процессе');
    });
  });

  test('рендерит колонку finished_date для других статусов без даты', async () => {
    const jobs = [
      { 
        job_id: 1, 
        status: 'pending', 
        finished_date: null, 
        summary: null 
      },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      const dateCell = screen.getByTestId('row-finished_date-1');
      expect(dateCell).toBeInTheDocument();
      expect(dateCell).toHaveTextContent('-');
    });
  });

  test('рендерит колонку summary с ошибками', async () => {
    const jobs = [
      { 
        job_id: 1, 
        status: 'failed', 
        finished_date: '2025-12-13T12:00:00Z', 
        summary: { errors: 5 } 
      },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      const summaryCell = screen.getByTestId('row-summary-1');
      expect(summaryCell).toBeInTheDocument();
      expect(summaryCell).toHaveTextContent('Есть проблемы (5)');
    });
  });

  test('рендерит колонку summary без ошибок', async () => {
    const jobs = [
      { 
        job_id: 1, 
        status: 'completed', 
        finished_date: '2025-12-13T12:00:00Z', 
        summary: { errors: 0 } 
      },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      const summaryCell = screen.getByTestId('row-summary-1');
      expect(summaryCell).toBeInTheDocument();
      expect(summaryCell).toHaveTextContent('Нет ошибок');
    });
  });

  test('рендерит колонку summary без summary объекта', async () => {
    const jobs = [
      { 
        job_id: 1, 
        status: 'pending', 
        finished_date: null, 
        summary: null 
      },
    ];
    syncApi.getJobs.mockResolvedValue(jobs);

    render(<SyncStatus />);
    await waitFor(() => {
      const summaryCell = screen.getByTestId('row-summary-1');
      expect(summaryCell).toBeInTheDocument();
      expect(summaryCell).toHaveTextContent('-');
    });
  });

  test('показывает кнопку повторить при ошибке загрузки', async () => {
    syncApi.getJobs.mockRejectedValue(new Error('API error'));
    render(<SyncStatus />);
    
    await waitFor(() => {
      expect(screen.getByText(/Не удалось загрузить данные синхронизации/i)).toBeInTheDocument();
      const retryButton = screen.getByText(/Повторить/i);
      expect(retryButton).toBeInTheDocument();
    });

    // Проверяем, что кнопка повторить вызывает fetchSyncJobs
    const retryButton = screen.getByText(/Повторить/i);
    syncApi.getJobs.mockResolvedValue([{ job_id: 1 }]);
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByTestId('mock-table')).toBeInTheDocument();
    });
  });

  test('показывает состояние обновления при refreshing', async () => {
    const jobs = [{ job_id: 1 }];
    syncApi.getJobs.mockResolvedValue(jobs);
    
    render(<SyncStatus />);
    await waitFor(() => screen.getByTestId('mock-table'));

    // Нажимаем кнопку обновления
    const refreshButton = screen.getByText(/Обновить/i);
    fireEvent.click(refreshButton);

    // Проверяем, что кнопка показывает состояние обновления
    await waitFor(() => {
      expect(screen.getByText(/Обновление.../i)).toBeInTheDocument();
    });
  });
});

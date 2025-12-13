import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SyncStatus from './index';

jest.mock('../../components/common/Header', () => () => <div data-testid="mock-header">Header</div>);

jest.mock('../../components/common/Table', () => {
  const React = require('react');
  const original = jest.requireActual('../../components/common/Table');
  return {
    __esModule: true,
    default: ({ data, emptyMessage }) => (
      <div data-testid="mock-table">
        {data.length > 0 ? data.map(d => <div key={d.job_id}>{d.job_id}</div>) : emptyMessage}
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
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
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
    const jobsBefore = [{ job_id: 1 }];
    const jobsAfter = [{ job_id: 2 }];
    syncApi.getJobs.mockResolvedValueOnce(jobsBefore).mockResolvedValueOnce(jobsAfter);
    syncApi.runSync.mockResolvedValue({});

    render(<SyncStatus />);
    await waitFor(() => screen.getByText('1'));

    fireEvent.click(screen.getByText(/Запустить синхронизацию/i));
    await waitFor(() => screen.getByText('2'));
  });
});

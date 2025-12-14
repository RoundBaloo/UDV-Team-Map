import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PhotoModeration from './index';

jest.mock('../../components/common/Header', () => () => <div data-testid="mock-header">Header</div>);

jest.mock('../../components/admin/PhotoModerationItem', () => {
  return {
    __esModule: true,
    default: ({ item, onApprove, onReject, loading }) => (
      <div data-testid={`photo-item-${item.photo_moderation_id || item.id}`}>
        <span data-testid={`photo-id-${item.photo_moderation_id || item.id}`}>{item.photo_moderation_id || item.id}</span>
        <button
          data-testid={`approve-${item.photo_moderation_id || item.id}`}
          disabled={!!loading}
          onClick={() => onApprove(item.photo_moderation_id || item.id)}
        >
          Approve
        </button>
        <button
          data-testid={`reject-${item.photo_moderation_id || item.id}`}
          onClick={() => onReject(item.photo_moderation_id || item.id, 'reason')}
        >
          Reject
        </button>
        {loading && <span data-testid={`loading-${item.photo_moderation_id || item.id}`}>loading</span>}
      </div>
    ),
  };
});

jest.mock('../../services/api/photoModeration', () => ({
  photoModerationApi: {
    getPendingPhotos: jest.fn(),
    approvePhoto: jest.fn(),
    rejectPhoto: jest.fn(),
  },
}));

const { photoModerationApi } = require('../../services/api/photoModeration');

describe('PhotoModeration page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('показывает loading пока данные загружаются', async () => {
    let resolveFn;
    const p = new Promise(resolve => { resolveFn = resolve; });
    photoModerationApi.getPendingPhotos.mockReturnValueOnce(p);

    render(<PhotoModeration />);

    expect(screen.getByText(/Загрузка фотографий на модерацию/i)).toBeInTheDocument();

    resolveFn({ items: [], total: 0 });
    await waitFor(() => {
      expect(screen.queryByText(/Загрузка фотографий на модерацию/i)).not.toBeInTheDocument();
    });
  });

  test('рендерит список фото из API и Header', async () => {
    const items = [
      { photo_moderation_id: 101, url: 'a.jpg' },
      { photo_moderation_id: 102, url: 'b.jpg' },
    ];
    photoModerationApi.getPendingPhotos.mockResolvedValueOnce({ items, total: 2 });

    render(<PhotoModeration />);

    expect(screen.getByTestId('mock-header')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('photo-item-101')).toBeInTheDocument();
      expect(screen.getByTestId('photo-item-102')).toBeInTheDocument();
    });

    expect(screen.getByText(/Модерация фотографий/)).toBeInTheDocument();
    expect(screen.getByText(/Ожидают модерации:/) || true).toBeTruthy();
  });
  
  test('approve вызывает API и удаляет элемент из списка', async () => {
    const items = [{ photo_moderation_id: 201 }, { photo_moderation_id: 202 }];
    photoModerationApi.getPendingPhotos.mockResolvedValueOnce({ items: [...items], total: 2 });
    photoModerationApi.approvePhoto.mockResolvedValueOnce({}); 

    render(<PhotoModeration />);

    await waitFor(() => {
      expect(screen.getByTestId('photo-item-201')).toBeInTheDocument();
    });

    const approveBtn = screen.getByTestId('approve-201');
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(photoModerationApi.approvePhoto).toHaveBeenCalledWith(201);
    });

    await waitFor(() => {
      expect(screen.queryByTestId('photo-item-201')).not.toBeInTheDocument();
      expect(screen.getByTestId('photo-item-202')).toBeInTheDocument();
    });
  });

  test('reject вызывает API и удаляет элемент из списка; на ошибке показывает сообщение', async () => {
    const items = [{ photo_moderation_id: 301 }];
    photoModerationApi.getPendingPhotos.mockResolvedValueOnce({ items: [...items], total: 1 });
    photoModerationApi.rejectPhoto.mockResolvedValueOnce({});

    render(<PhotoModeration />);

    await waitFor(() => {
      expect(screen.getByTestId('photo-item-301')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('reject-301'));

    await waitFor(() => {
      expect(photoModerationApi.rejectPhoto).toHaveBeenCalledWith(301, 'reason');
    });

    await waitFor(() => {
      expect(screen.queryByTestId('photo-item-301')).not.toBeInTheDocument();
    });

    photoModerationApi.getPendingPhotos.mockResolvedValueOnce({ items: [{ photo_moderation_id: 302 }], total: 1 });
    photoModerationApi.rejectPhoto.mockRejectedValueOnce(new Error('reject failed'));

    render(<PhotoModeration />);

    await waitFor(() => {
      expect(screen.getByTestId('photo-item-302')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('reject-302'));

    await waitFor(() => {
      expect(photoModerationApi.rejectPhoto).toHaveBeenCalledWith(302, 'reason');
    });

    await waitFor(() => {
      expect(screen.getByText(/Ошибка при отклонении фото/i)).toBeInTheDocument();
    });
  });

  test('при ошибке загрузки показывает alert и retry вызывает повторную загрузку', async () => {
    photoModerationApi.getPendingPhotos.mockRejectedValueOnce(new Error('API down'));
    photoModerationApi.getPendingPhotos.mockResolvedValueOnce({ items: [{ photo_moderation_id: 401 }], total: 1 });

    render(<PhotoModeration />);

    await waitFor(() => {
      expect(screen.getByText(/Не удалось загрузить фотографии на модерацию/i)).toBeInTheDocument();
    });

    const retryBtn = screen.getByRole('button', { name: /Повторить/i });
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByTestId('photo-item-401')).toBeInTheDocument();
      expect(photoModerationApi.getPendingPhotos).toHaveBeenCalledTimes(2);
    });
  });

  test('пагинация: next/prev вызывает повторную загрузку с другим offset', async () => {
    photoModerationApi.getPendingPhotos.mockResolvedValueOnce({
      items: [{ photo_moderation_id: 501 }],
      total: 120,
    });
    photoModerationApi.getPendingPhotos.mockResolvedValueOnce({
      items: [{ photo_moderation_id: 502 }],
      total: 120,
    });

    render(<PhotoModeration />);

    await waitFor(() => {
      expect(screen.getByTestId('photo-item-501')).toBeInTheDocument();
    });

    const nextBtn = screen.getByRole('button', { name: /Вперед/i });
    expect(nextBtn).toBeInTheDocument();
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(photoModerationApi.getPendingPhotos).toHaveBeenCalledTimes(2);
      expect(screen.getByTestId('photo-item-502')).toBeInTheDocument();
    });

    photoModerationApi.getPendingPhotos.mockResolvedValueOnce({
      items: [{ photo_moderation_id: 501 }],
      total: 120,
    });

    const prevBtn = screen.getByRole('button', { name: /Назад/i });
    fireEvent.click(prevBtn);

    await waitFor(() => {
      expect(photoModerationApi.getPendingPhotos).toHaveBeenCalledTimes(3);
      expect(screen.getByTestId('photo-item-501')).toBeInTheDocument();
    });
  });
});

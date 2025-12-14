import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import OrgStructure from './index';
import { orgUnitsApi } from '../../services/api/orgUnits';
import '@testing-library/jest-dom';


jest.mock('../../services/api/orgUnits', () => ({
  orgUnitsApi: {
    getOrgStructure: jest.fn(),
  },
}));

jest.mock('../../components/common/Header', () => () => <div data-testid="mock-header">Header</div>);
jest.mock('../../components/org-structure/DepartmentList', () => ({ selectedUnitId }) => (
  <div data-testid="department-list" data-selected={selectedUnitId}></div>
));

describe('OrgStructure page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    sessionStorage.clear();
  });

  test('рендерит Header, заголовок и DepartmentList', async () => {
    orgUnitsApi.getOrgStructure.mockResolvedValueOnce([{ id: 1, name: 'Unit 1' }]);

    render(<OrgStructure />);

    expect(screen.getByTestId('mock-header')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('department-list')).toBeInTheDocument();
    });
  });

  test('читает выбранное подразделение из sessionStorage и передаёт selectedUnitId в DepartmentList', async () => {
    sessionStorage.setItem('selectedOrgUnit', JSON.stringify({ org_unit_id: 42 }));
    orgUnitsApi.getOrgStructure.mockResolvedValueOnce([{ id: 1, name: 'Unit 1' }]);

    render(<OrgStructure />);

    await waitFor(() => screen.getByTestId('department-list'));

    await waitFor(() => {
      expect(screen.getByTestId('department-list').getAttribute('data-selected')).toBe('42');
    });

    expect(sessionStorage.getItem('selectedOrgUnit')).toBeNull();
  });

  test('показывает индикатор загрузки, если loading === true', async () => {
    let resolveFn;
    const promise = new Promise(resolve => { resolveFn = resolve; });
    orgUnitsApi.getOrgStructure.mockReturnValueOnce(promise);

    render(<OrgStructure />);

    expect(screen.getByText(/Загрузка организационной структуры/i)).toBeInTheDocument();

    resolveFn([{ id: 1, name: 'Unit 1' }]);
    await waitFor(() => screen.getByTestId('department-list'));
  });

  test('показывает ошибку и кнопку повторить при падении API', async () => {
    orgUnitsApi.getOrgStructure.mockRejectedValueOnce(new Error('API Error'));

    render(<OrgStructure />);

    await waitFor(() => {
      expect(screen.getByText(/Не удалось загрузить структуру/i)).toBeInTheDocument();
      expect(screen.getByText(/Повторить/)).toBeInTheDocument();
    });
  });
  
  test('нажатие кнопки "Повторить" повторно вызывает загрузку', async () => {
    orgUnitsApi.getOrgStructure.mockRejectedValueOnce(new Error('API Error'));
    orgUnitsApi.getOrgStructure.mockResolvedValueOnce([{ id: 1, name: 'Unit 1' }]);

    render(<OrgStructure />);

    await waitFor(() => screen.getByText(/Повторить/));

    fireEvent.click(screen.getByText(/Повторить/));

    await waitFor(() => {
      expect(screen.getByTestId('department-list')).toBeInTheDocument();
    });
  });
});

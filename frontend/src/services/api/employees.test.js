import { employeesApi } from './employees';
import { apiClient } from './apiClient';

jest.mock('../../utils/apiHelpers', () => ({
  buildEndpoint: (endpoint, params) => `/api/test/${params.employee_id}`,
  buildQueryString: (params) => (params && Object.keys(params).length ? '?q=1' : ''),
}));

describe('employeesApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('getEmployees вызывает apiClient.get с query', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue([{ id: 1 }]);

    const res = await employeesApi.getEmployees({ page: 1 });
    expect(apiClient.get).toHaveBeenCalledWith('/api/employees/?q=1');
    expect(res).toEqual([{ id: 1 }]);
  });

  test('getEmployee использует buildEndpoint и вызывает apiClient.get', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue({ id: 1 });

    const res = await employeesApi.getEmployee(1);
    expect(apiClient.get).toHaveBeenCalledWith('/api/test/1');
    expect(res).toEqual({ id: 1 });
  });

  test('updateEmployee вызывает patch с правильным endpoint и данными', async () => {
    jest.spyOn(apiClient, 'patch').mockResolvedValue({ success: true });

    const res = await employeesApi.updateEmployee(1, { name: 'John' });
    expect(apiClient.patch).toHaveBeenCalledWith('/api/test/1', { name: 'John' });
    expect(res).toEqual({ success: true });
  });

  test('searchSkills вызывает endpoint с query', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue([{ skill: 'JS' }]);
    const res = await employeesApi.searchSkills({ q: 'JS' });
    expect(apiClient.get).toHaveBeenCalledWith('/api/employees/skills/search?q=1');
    expect(res).toEqual([{ skill: 'JS' }]);
  });
});

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

  test('getCurrentEmployee вызывает apiClient.get с ME endpoint', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue({ id: 1, name: 'Current User' });

    const res = await employeesApi.getCurrentEmployee();
    expect(apiClient.get).toHaveBeenCalledWith('/api/employees/me');
    expect(res).toEqual({ id: 1, name: 'Current User' });
  });

  test('updateMe вызывает apiClient.patch с ME endpoint и данными', async () => {
    jest.spyOn(apiClient, 'patch').mockResolvedValue({ success: true });

    const employeeData = { name: 'Updated Name', title: 'Developer' };
    const res = await employeesApi.updateMe(employeeData);
    expect(apiClient.patch).toHaveBeenCalledWith('/api/employees/me', employeeData);
    expect(res).toEqual({ success: true });
  });

  test('searchTitles вызывает endpoint с query', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue([{ title: 'Developer' }]);
    const res = await employeesApi.searchTitles({ q: 'Dev' });
    expect(apiClient.get).toHaveBeenCalledWith('/api/employees/titles/search?q=1');
    expect(res).toEqual([{ title: 'Developer' }]);
  });

  test('searchTitles вызывает endpoint без query, если params пустые', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue([{ title: 'All Titles' }]);
    const res = await employeesApi.searchTitles({});
    expect(apiClient.get).toHaveBeenCalledWith('/api/employees/titles/search');
    expect(res).toEqual([{ title: 'All Titles' }]);
  });
});

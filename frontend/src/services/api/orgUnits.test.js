import { orgUnitsApi } from './orgUnits';
import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../../utils/constants';

jest.mock('../../utils/apiHelpers', () => ({
  buildEndpoint: (endpoint, params) => `/api/test/${params.org_unit_id}`,
  buildQueryString: (params) =>
    params && Object.keys(params).length ? '?q=1' : '',
}));

describe('orgUnitsApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('getOrgStructure вызывает apiClient.get с константой LIST', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue({ tree: [] });

    const res = await orgUnitsApi.getOrgStructure();

    expect(apiClient.get).toHaveBeenCalledWith(API_ENDPOINTS.ORG_UNITS.LIST);
    expect(res).toEqual({ tree: [] });
  });

  test('searchOrgUnits формирует endpoint /api/org-units/search + query и вызывает apiClient.get', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue([{ id: 1 }]);

    const res = await orgUnitsApi.searchOrgUnits({ q: 'term' });

    expect(apiClient.get).toHaveBeenCalledWith('/api/org-units/search?q=1');
    expect(res).toEqual([{ id: 1 }]);
  });

  test('getDomains вызывает apiClient.get с /api/org-units/domains', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue(['domain1', 'domain2']);

    const res = await orgUnitsApi.getDomains();

    expect(apiClient.get).toHaveBeenCalledWith('/api/org-units/domains');
    expect(res).toEqual(['domain1', 'domain2']);
  });

  test('searchLegalEntities формирует endpoint /api/org-units/legal-entities/search + query и вызывает apiClient.get', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue([{ id: 2 }]);

    const res = await orgUnitsApi.searchLegalEntities({ q: 'x' });

    expect(apiClient.get).toHaveBeenCalledWith('/api/org-units/legal-entities/search?q=1');
    expect(res).toEqual([{ id: 2 }]);
  });
  
  test('getUnitEmployees использует buildEndpoint и добавляет queryString', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue([{ id: 10 }]);

    const res = await orgUnitsApi.getUnitEmployees(42, { page: 1 });

    expect(apiClient.get).toHaveBeenCalledWith('/api/test/42?q=1');
    expect(res).toEqual([{ id: 10 }]);
  });

  test('getUnitEmployees без params вызывает apiClient.get без query', async () => {
    jest.spyOn(apiClient, 'get').mockResolvedValue([{ id: 11 }]);

    const res = await orgUnitsApi.getUnitEmployees(7);

    expect(apiClient.get).toHaveBeenCalledWith('/api/test/7');
    expect(res).toEqual([{ id: 11 }]);
  });
});

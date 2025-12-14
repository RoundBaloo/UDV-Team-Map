// src/utils/mockData.test.js
import {
  mockEmployee,
  mockCurrentUser,
  mockTeam,
  mockEmployeesByUnit,
  getEmployeesByUnitId,
  getManagerByUnitId,
  getMembersByUnitId,
  getEmployeeCountByUnitId,
  mockOrgStructure
} from './mockData';

describe('mockData', () => {
  test('mockEmployee содержит корректные поля', () => {
    expect(mockEmployee).toHaveProperty('id', 1);
    expect(mockEmployee).toHaveProperty('first_name', 'Иван');
    expect(mockEmployee).toHaveProperty('last_name', 'Иванов');
    expect(mockEmployee).toHaveProperty('email', 'ivanov@udv-group.ru');
  });

  test('mockCurrentUser наследует mockEmployee и имеет другие поля', () => {
    expect(mockCurrentUser.id).toBe(2);
    expect(mockCurrentUser.first_name).toBe('Петр');
    expect(mockCurrentUser.is_admin).toBe(true);
  });

  test('mockTeam содержит корректного менеджера и членов', () => {
    expect(mockTeam.manager).toHaveProperty('id', 2);
    expect(mockTeam.members.length).toBeGreaterThan(0);
  });

  describe('getEmployeesByUnitId', () => {
    test('возвращает массив сотрудников для существующего подразделения', () => {
      const employees = getEmployeesByUnitId(4);
      expect(employees).toEqual(mockEmployeesByUnit[4]);
    });

    test('возвращает пустой массив для несуществующего подразделения', () => {
      const employees = getEmployeesByUnitId(999);
      expect(employees).toEqual([]);
    });
  });

  describe('getManagerByUnitId', () => {
    test('возвращает менеджера подразделения', () => {
      const manager = getManagerByUnitId(4);
      expect(manager).toHaveProperty('is_manager', true);
      expect(manager.id).toBe(1001);
    });

    test('возвращает null если менеджера нет', () => {
      const manager = getManagerByUnitId(999);
      expect(manager).toBeNull();
    });
  });

  describe('getMembersByUnitId', () => {
    test('возвращает только участников без менеджера', () => {
      const members = getMembersByUnitId(4);
      expect(members.every(emp => !emp.is_manager)).toBe(true);
      expect(members.length).toBe(mockEmployeesByUnit[4].length - 1);
    });

    test('возвращает пустой массив для подразделения без сотрудников', () => {
      const members = getMembersByUnitId(999);
      expect(members).toEqual([]);
    });
  });

  describe('getEmployeeCountByUnitId', () => {
    test('возвращает количество сотрудников', () => {
      expect(getEmployeeCountByUnitId(4)).toBe(mockEmployeesByUnit[4].length);
    });

    test('возвращает 0 для несуществующего подразделения', () => {
      expect(getEmployeeCountByUnitId(999)).toBe(0);
    });
  });

  test('mockOrgStructure содержит departments', () => {
    expect(mockOrgStructure).toHaveProperty('departments');
    expect(Array.isArray(mockOrgStructure.departments)).toBe(true);
    expect(mockOrgStructure.departments[0]).toHaveProperty('id', 1);
  });

  test('mockEmployeesByUnit содержит несколько подразделений', () => {
    const unitIds = Object.keys(mockEmployeesByUnit).map(id => Number(id));
    expect(unitIds.length).toBeGreaterThan(0);
    unitIds.forEach(id => {
      expect(Array.isArray(mockEmployeesByUnit[id])).toBe(true);
    });
  });
});

// src/hooks/useTeam.test.js
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';

// Мокаем useParams отдельно, чтобы управлять id в каждом тесте
jest.mock('react-router-dom', () => ({ useParams: jest.fn() }));

// Мокаем модуль orgUnits (импортируется динамически в хук)
jest.mock('../services/api/orgUnits', () => ({
  orgUnitsApi: {
    getOrgStructure: jest.fn(),
  },
}));

// Мокаем mockData — будем контролировать getEmployeesByUnitId и прочие функции
jest.mock('../utils/mockData', () => ({
  getEmployeesByUnitId: jest.fn(),
  getManagerByUnitId: jest.fn(),
  getMembersByUnitId: jest.fn(),
  mockOrgStructure: {
    id: 1,
    name: 'Root Mock',
    children: [
      {
        id: 7,
        name: 'Mock Team 7',
        children: [],
      },
    ],
  },
}));

// Импорты после jest.mock чтобы получить мок-референсы
const { useParams } = require('react-router-dom');
const { orgUnitsApi } = require('../services/api/orgUnits');
const { getEmployeesByUnitId, getManagerByUnitId, getMembersByUnitId, mockOrgStructure } = require('../utils/mockData');
const { useTeam } = require('./useTeam');

// Компонент-обёртка для вывода состояния хука в DOM
function TestComponent() {
  const { team, loading, manager, members, breadcrumbPath } = useTeam();

  return (
    <div>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="team">{JSON.stringify(team)}</div>
      <div data-testid="manager">{JSON.stringify(manager)}</div>
      <div data-testid="members">{JSON.stringify(members)}</div>
      <div data-testid="breadcrumbs">{JSON.stringify(breadcrumbPath)}</div>
    </div>
  );
}

describe('useTeam hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // По умолчанию возврат пустых сотрудников
    getEmployeesByUnitId.mockImplementation(() => []);
    getManagerByUnitId.mockImplementation(() => null);
    getMembersByUnitId.mockImplementation(() => []);
  });

  test('when orgUnitsApi returns structure and team node exists -> sets team, manager, members and breadcrumbs', async () => {
    // Подставим id команды 4
    useParams.mockReturnValue({ id: '4' });

    // Подготовим структуру с нужным узлом (root id 1 будет отфильтрован из breadcrumbs)
    const orgStructure = {
      id: 1,
      name: 'Root',
      children: [
        {
          id: 4,
          name: 'Team 4',
          description: 'Описание команды 4',
          children: [],
        },
      ],
    };

    // orgUnitsApi возвращает структуру
    orgUnitsApi.getOrgStructure.mockResolvedValueOnce(orgStructure);

    // Сотрудники для unit 4
    const employees = [{ id: 101 }, { id: 102 }];
    const manager = { id: 101, name: 'Manager 101' };
    const members = [{ id: 102, name: 'Member 102' }];

    getEmployeesByUnitId.mockImplementation((unitId) => (unitId === 4 ? employees : []));
    getManagerByUnitId.mockImplementation((unitId) => (unitId === 4 ? manager : null));
    getMembersByUnitId.mockImplementation((unitId) => (unitId === 4 ? members : []));

    render(<TestComponent />);

    // Ждём, пока loading станет false
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    // Проверяем team
    const team = JSON.parse(screen.getByTestId('team').textContent);
    expect(team).toBeTruthy();
    expect(team.id).toBe(4);
    expect(team.name).toBe('Team 4');
    expect(team.description).toBe('Описание команды 4');
    expect(team.employee_count).toBe(2);

    // Проверяем manager и members
    expect(JSON.parse(screen.getByTestId('manager').textContent)).toEqual(manager);
    expect(JSON.parse(screen.getByTestId('members').textContent)).toEqual(members);

    // Breadcrumbs: root (id 1) должен быть отфильтрован -> останется только узел 4
    const breadcrumbs = JSON.parse(screen.getByTestId('breadcrumbs').textContent);
    expect(Array.isArray(breadcrumbs)).toBe(true);
    // Ожидаем, что в breadcrumbs есть элемент с id 4 (либо org_unit_id 4)
    const ids = breadcrumbs.map(it => it.org_unit_id || it.id);
    expect(ids).toContain(4);
    expect(ids).not.toContain(1);
  });

  test('when orgUnitsApi fails -> uses mockOrgStructure and sets breadcrumbPath from mockOrgStructure', async () => {
    useParams.mockReturnValue({ id: '7' });

    // orgUnitsApi откажет (симулируем reject)
    orgUnitsApi.getOrgStructure.mockRejectedValueOnce(new Error('network'));

    // Для mockOrgStructure (см. jest.mock выше) уже есть узел id 7
    // Заполним сотрудников из mockData для unit 7
    const employees = [{ id: 201 }, { id: 202 }, { id: 203 }];
    const manager = { id: 201, name: 'Mgr 201' };
    const members = [{ id: 202 }, { id: 203 }];

    getEmployeesByUnitId.mockImplementation((unitId) => (unitId === 7 ? employees : []));
    getManagerByUnitId.mockImplementation((unitId) => (unitId === 7 ? manager : null));
    getMembersByUnitId.mockImplementation((unitId) => (unitId === 7 ? members : []));

    render(<TestComponent />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    // Проверяем, что команда была сформирована из mockOrgStructure node 7
    const team = JSON.parse(screen.getByTestId('team').textContent);
    expect(team).toBeTruthy();
    expect(team.id).toBe(7);
    expect(team.name).toBe('Mock Team 7');
    expect(team.employee_count).toBe(3);

    // Breadcrumbs должны быть получены из mockOrgStructure (root 1 отфильтровывается)
    const breadcrumbs = JSON.parse(screen.getByTestId('breadcrumbs').textContent);
    const ids = breadcrumbs.map(it => it.org_unit_id || it.id);
    expect(ids).toContain(7);
    expect(ids).not.toContain(1);
  });

  test('when team node not found but employees exist -> builds synthetic team with Команда #id', async () => {
    const UNIT = 99;
    useParams.mockReturnValue({ id: String(UNIT) });

    // orgUnitsApi вернёт структуру, но без узла 99
    orgUnitsApi.getOrgStructure.mockResolvedValueOnce({
      id: 1,
      name: 'Root',
      children: [{ id: 2, name: 'Team 2' }],
    });

    // Для unit 99 есть сотрудники (но нет узла в orgStructure)
    const employees = [{ id: 301 }, { id: 302 }, { id: 303 }, { id: 304 }];
    getEmployeesByUnitId.mockImplementation((unitId) => (unitId === UNIT ? employees : []));
    getManagerByUnitId.mockImplementation((unitId) => (unitId === UNIT ? { id: 301 } : null));
    getMembersByUnitId.mockImplementation((unitId) => (unitId === UNIT ? employees.slice(1) : []));

    render(<TestComponent />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    const team = JSON.parse(screen.getByTestId('team').textContent);
    expect(team).toBeTruthy();
    expect(team.id).toBe(UNIT);
    expect(team.name).toBe(`Команда #${UNIT}`);
    expect(team.employee_count).toBe(4);

    // manager and members
    expect(JSON.parse(screen.getByTestId('manager').textContent)).toEqual({ id: 301 });
    expect(JSON.parse(screen.getByTestId('members').textContent).length).toBe(3);
  });

  test('when no team node and no employees -> leaves team null and loading false', async () => {
    useParams.mockReturnValue({ id: '555' });

    orgUnitsApi.getOrgStructure.mockResolvedValueOnce({
      id: 1,
      name: 'Root',
      children: [{ id: 2, name: 'Team 2' }],
    });

    // Для unit 555 возвращаем пустые массивы (по умолчанию моки возвращают [])
    getEmployeesByUnitId.mockImplementation(() => []);
    getManagerByUnitId.mockImplementation(() => null);
    getMembersByUnitId.mockImplementation(() => []);

    render(<TestComponent />);

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('false'));

    const team = JSON.parse(screen.getByTestId('team').textContent);
    expect(team).toBe(null);
    expect(screen.getByTestId('manager').textContent).toBe('null');
    expect(screen.getByTestId('members').textContent).toBe('[]');
    // breadcrumbs may be []
    const breadcrumbs = JSON.parse(screen.getByTestId('breadcrumbs').textContent);
    expect(Array.isArray(breadcrumbs)).toBe(true);
  });
});

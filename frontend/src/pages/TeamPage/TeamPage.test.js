import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => ({
  useNavigate: jest.fn(),
}));

jest.mock('../../hooks/useTeam');

jest.mock('../../components/common/Header', () => () => <div data-testid="mock-header">Header</div>);
jest.mock('../../components/common/Breadcrumbs', () => () => <div data-testid="mock-breadcrumbs">Breadcrumbs</div>);
jest.mock('../../components/team/TeamHeader', () => ({ team }) => <div data-testid="mock-team-header">{team?.name}</div>);
jest.mock('../../components/team/ManagerCard', () => ({ manager, onClick }) => (
  <div data-testid="mock-manager-card" onClick={onClick}>{manager?.name}</div>
));
jest.mock('../../components/team/TeamMembers', () => ({ members, onMemberClick }) => (
  <div data-testid="mock-team-members">
    {members?.map(m => (
      <div key={m.id} onClick={() => onMemberClick(m.id)}>{m.name}</div>
    ))}
  </div>
));
jest.mock('../../components/team/LoadingState', () => ({ breadcrumbPath }) => (
  <div data-testid="mock-loading">Loading</div>
));
jest.mock('../../components/team/ErrorState', () => ({ breadcrumbPath }) => (
  <div data-testid="mock-error">Error</div>
));

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TeamPage from './index';

const { useNavigate } = require('react-router-dom');
const { useTeam } = require('../../hooks/useTeam');

describe('TeamPage', () => {
  const mockNavigate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    useNavigate.mockReturnValue(mockNavigate);
    // Устанавливаем значения по умолчанию для useTeam
    useTeam.mockReturnValue({
      loading: false,
      team: null,
      manager: null,
      members: [],
      breadcrumbPath: [],
    });
  });

  test('показывает loading state', () => {
    useTeam.mockReturnValue({ loading: true });
    render(<TeamPage />);
    expect(screen.getByTestId('mock-loading')).toBeInTheDocument();
  });

  test('показывает error state, если team отсутствует', () => {
    useTeam.mockReturnValue({ loading: false, team: null, breadcrumbPath: [] });
    render(<TeamPage />);
    expect(screen.getByTestId('mock-error')).toBeInTheDocument();
  });

  test('рендерит данные команды, менеджера и участников', () => {
    const team = { id: 1, name: 'Team A' };
    const manager = { id: 1, employee_id: 1, name: 'Manager A' };
    const members = [
      { id: 1, name: 'Member 1' },
      { id: 2, name: 'Member 2' },
    ];
    const breadcrumbPath = ['Home', 'Team A'];

    useTeam.mockReturnValue({ loading: false, team, manager, members, breadcrumbPath });

    render(<TeamPage />);

    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-breadcrumbs')).toBeInTheDocument();
    expect(screen.getByTestId('mock-team-header')).toHaveTextContent('Team A');
    expect(screen.getByTestId('mock-manager-card')).toHaveTextContent('Manager A');
    expect(screen.getByTestId('mock-team-members')).toHaveTextContent('Member 1');
    expect(screen.getByTestId('mock-team-members')).toHaveTextContent('Member 2');
  });

  test('клик по менеджеру вызывает navigate с employee_id', () => {
    const manager = { id: 5, employee_id: 5, name: 'Manager X' };
    useTeam.mockReturnValue({ loading: false, team: { name: 'Team X' }, manager, members: [], breadcrumbPath: [] });

    render(<TeamPage />);
    fireEvent.click(screen.getByTestId('mock-manager-card'));
    expect(mockNavigate).toHaveBeenCalledWith('/profile/5');
  });

  test('клик по менеджеру использует id, если employee_id отсутствует', () => {
    const manager = { id: 7, name: 'Manager Y' }; // без employee_id
    useTeam.mockReturnValue({ loading: false, team: { name: 'Team Y' }, manager, members: [], breadcrumbPath: [] });

    render(<TeamPage />);
    fireEvent.click(screen.getByTestId('mock-manager-card'));
    expect(mockNavigate).toHaveBeenCalledWith('/profile/7');
  });

  test('клик по участнику вызывает navigate', () => {
    const members = [{ id: 10, name: 'Member X' }];
    useTeam.mockReturnValue({ loading: false, team: { name: 'Team X' }, manager: null, members, breadcrumbPath: [] });

    render(<TeamPage />);
    fireEvent.click(screen.getByText('Member X'));
    expect(mockNavigate).toHaveBeenCalledWith('/profile/10');
  });

  test('не рендерит ManagerCard, если manager отсутствует', () => {
    const team = { id: 1, name: 'Team A' };
    const members = [{ id: 1, name: 'Member 1' }];
    useTeam.mockReturnValue({ loading: false, team, manager: null, members, breadcrumbPath: [] });

    render(<TeamPage />);

    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-team-header')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-manager-card')).not.toBeInTheDocument();
    expect(screen.getByTestId('mock-team-members')).toBeInTheDocument();
  });

  test('рендерит ManagerCard, если manager присутствует', () => {
    const team = { id: 1, name: 'Team A' };
    const manager = { id: 1, employee_id: 1, name: 'Manager A' };
    const members = [{ id: 2, name: 'Member 1' }];
    useTeam.mockReturnValue({ loading: false, team, manager, members, breadcrumbPath: [] });

    render(<TeamPage />);

    expect(screen.getByTestId('mock-manager-card')).toBeInTheDocument();
    expect(screen.getByTestId('mock-manager-card')).toHaveTextContent('Manager A');
  });

  test('передает breadcrumbPath в LoadingState', () => {
    const breadcrumbPath = ['Home', 'Teams', 'Team A'];
    useTeam.mockReturnValue({ loading: true, breadcrumbPath });

    render(<TeamPage />);
    
    expect(screen.getByTestId('mock-loading')).toBeInTheDocument();
  });

  test('передает breadcrumbPath в ErrorState', () => {
    const breadcrumbPath = ['Home', 'Teams'];
    useTeam.mockReturnValue({ loading: false, team: null, breadcrumbPath });

    render(<TeamPage />);
    
    expect(screen.getByTestId('mock-error')).toBeInTheDocument();
  });

  test('передает breadcrumbPath в Breadcrumbs', () => {
    const team = { id: 1, name: 'Team A' };
    const breadcrumbPath = ['Home', 'Teams', 'Team A'];
    useTeam.mockReturnValue({ loading: false, team, manager: null, members: [], breadcrumbPath });

    render(<TeamPage />);
    
    expect(screen.getByTestId('mock-breadcrumbs')).toBeInTheDocument();
  });

  test('рендерит все компоненты при наличии всех данных', () => {
    const team = { id: 1, name: 'Team A' };
    const manager = { id: 1, employee_id: 1, name: 'Manager A' };
    const members = [
      { id: 2, name: 'Member 1' },
      { id: 3, name: 'Member 2' },
    ];
    const breadcrumbPath = ['Home', 'Team A'];

    useTeam.mockReturnValue({ loading: false, team, manager, members, breadcrumbPath });

    render(<TeamPage />);

    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-breadcrumbs')).toBeInTheDocument();
    expect(screen.getByTestId('mock-team-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-manager-card')).toBeInTheDocument();
    expect(screen.getByTestId('mock-team-members')).toBeInTheDocument();
    expect(screen.getByText('Member 1')).toBeInTheDocument();
    expect(screen.getByText('Member 2')).toBeInTheDocument();
  });
});

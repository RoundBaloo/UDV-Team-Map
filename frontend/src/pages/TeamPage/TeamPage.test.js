import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';

// --------------------
// SAFE MOCKS (no real deps)
// --------------------

jest.mock('react-router-dom', () => ({
  useNavigate: jest.fn(),
}));

jest.mock('../../hooks/useTeam', () => ({
  useTeam: jest.fn(),
}));

jest.mock('../../components/common/Header', () => () =>
  <div data-testid="mock-header">Header</div>
);

jest.mock('../../components/common/Breadcrumbs', () => () =>
  <div data-testid="mock-breadcrumbs">Breadcrumbs</div>
);

jest.mock('../../components/team/TeamHeader', () => ({ team }) =>
  <div data-testid="mock-team-header">{team?.name}</div>
);

jest.mock('../../components/team/ManagerCard', () => ({ manager, onClick }) => (
  <div data-testid="mock-manager-card" onClick={onClick}>
    {manager?.name}
  </div>
));

jest.mock('../../components/team/TeamMembers', () => ({ members, onMemberClick }) => (
  <div data-testid="mock-team-members">
    {members?.map(m => (
      <div key={m.id} onClick={() => onMemberClick(m.id)}>
        {m.name}
      </div>
    ))}
  </div>
));

jest.mock('../../components/team/LoadingState', () => () =>
  <div data-testid="mock-loading">Loading</div>
);

jest.mock('../../components/team/ErrorState', () => () =>
  <div data-testid="mock-error">Error</div>
);

// --------------------
// imports AFTER mocks
// --------------------

import TeamPage from './index';
import { useNavigate } from 'react-router-dom';
import { useTeam } from '../../hooks/useTeam';

// --------------------
// tests
// --------------------

describe('TeamPage', () => {
  const mockNavigate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    useNavigate.mockReturnValue(mockNavigate);

    useTeam.mockReturnValue({
      loading: false,
      team: null,
      manager: null,
      members: [],
      breadcrumbPath: [],
    });
  });

  test('renders loading state', () => {
    useTeam.mockReturnValue({
      loading: true,
      breadcrumbPath: [],
    });

    render(<TeamPage />);

    expect(screen.getByTestId('mock-loading')).toBeInTheDocument();
  });

  test('renders error state when team is null', () => {
    useTeam.mockReturnValue({
      loading: false,
      team: null,
      breadcrumbPath: [],
    });

    render(<TeamPage />);

    expect(screen.getByTestId('mock-error')).toBeInTheDocument();
  });

  test('renders team, manager and members', () => {
    useTeam.mockReturnValue({
      loading: false,
      team: { id: 1, name: 'Team A' },
      manager: { id: 1, employee_id: 1, name: 'Manager A' },
      members: [
        { id: 1, name: 'Member 1' },
        { id: 2, name: 'Member 2' },
      ],
      breadcrumbPath: ['Home', 'Team A'],
    });

    render(<TeamPage />);

    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-breadcrumbs')).toBeInTheDocument();
    expect(screen.getByTestId('mock-team-header')).toHaveTextContent('Team A');
    expect(screen.getByTestId('mock-manager-card')).toHaveTextContent('Manager A');
    expect(screen.getByText('Member 1')).toBeInTheDocument();
    expect(screen.getByText('Member 2')).toBeInTheDocument();
  });

  test('manager click navigates by employee_id', () => {
    useTeam.mockReturnValue({
      loading: false,
      team: { name: 'Team X' },
      manager: { id: 5, employee_id: 5, name: 'Manager X' },
      members: [],
      breadcrumbPath: [],
    });

    render(<TeamPage />);

    fireEvent.click(screen.getByTestId('mock-manager-card'));

    expect(mockNavigate).toHaveBeenCalledWith('/profile/5');
  });

  test('manager click falls back to id', () => {
    useTeam.mockReturnValue({
      loading: false,
      team: { name: 'Team Y' },
      manager: { id: 7, name: 'Manager Y' },
      members: [],
      breadcrumbPath: [],
    });

    render(<TeamPage />);

    fireEvent.click(screen.getByTestId('mock-manager-card'));

    expect(mockNavigate).toHaveBeenCalledWith('/profile/7');
  });

  test('member click navigates to profile', () => {
    useTeam.mockReturnValue({
      loading: false,
      team: { name: 'Team X' },
      manager: null,
      members: [{ id: 10, name: 'Member X' }],
      breadcrumbPath: [],
    });

    render(<TeamPage />);

    fireEvent.click(screen.getByText('Member X'));

    expect(mockNavigate).toHaveBeenCalledWith('/profile/10');
  });

  test('does not render ManagerCard if manager is null', () => {
    useTeam.mockReturnValue({
      loading: false,
      team: { id: 1, name: 'Team A' },
      manager: null,
      members: [{ id: 1, name: 'Member 1' }],
      breadcrumbPath: [],
    });

    render(<TeamPage />);

    expect(screen.queryByTestId('mock-manager-card')).not.toBeInTheDocument();
  });
});
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import Breadcrumbs from '../../components/common/Breadcrumbs';
import TeamHeader from '../../components/team/TeamHeader';
import ManagerCard from '../../components/team/ManagerCard';
import TeamMembers from '../../components/team/TeamMembers';
import LoadingState from '../../components/team/LoadingState';
import ErrorState from '../../components/team/ErrorState';
import { useTeam } from '../../hooks/useTeam';
import './TeamPage.css';

const TeamPage = () => {
  const { team, loading, manager, members, breadcrumbPath } = useTeam();
  const navigate = useNavigate();

  const handleEmployeeClick = employeeId => {
    navigate(`/profile/${employeeId}`);
  };

  const handleManagerClick = managerId => {
    navigate(`/profile/${managerId}`);
  };

  if (loading) {
    return <LoadingState breadcrumbPath={breadcrumbPath} />;
  }

  if (!team) {
    return <ErrorState breadcrumbPath={breadcrumbPath} />;
  }

  return (
    <div className="team-page">
      <Header />
      <Breadcrumbs customPath={breadcrumbPath} />
      
      <main className="team-main">
        <div className="container">
          <TeamHeader team={team} />

          <div className="team-description">
            <p>{team.description}</p>
          </div>

          {manager && (
            <ManagerCard
              manager={manager}
              onClick={() => handleManagerClick(manager.employee_id || manager.id)}
            />
          )}

          <TeamMembers
            members={members}
            onMemberClick={handleEmployeeClick}
          />
        </div>
      </main>
    </div>
  );
};

export default TeamPage;
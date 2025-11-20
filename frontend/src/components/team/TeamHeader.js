import React from 'react';

const TeamHeader = ({ team }) => {
  return (
    <div className="team-header">
      <h1>{team.name}</h1>
      <div className="team-stats">
        Участников: {team.employee_count}
      </div>
    </div>
  );
};

export default TeamHeader;
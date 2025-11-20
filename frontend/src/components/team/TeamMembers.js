import React from 'react';
import MemberCard from './MemberCard';

const TeamMembers = ({ members, onMemberClick }) => {
  if (members.length === 0) {
    return null;
  }

  return (
    <div className="team-section">
      <h2>Участники команды ({members.length})</h2>
      <div className="members-grid">
        {members.map(member => (
          <MemberCard
            key={member.employee_id || member.id}
            member={member}
            onClick={() => onMemberClick(member.employee_id || member.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default TeamMembers;
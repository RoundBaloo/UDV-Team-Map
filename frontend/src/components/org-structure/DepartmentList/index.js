import React from 'react';
import CollapsibleSection from '../CollapsibleSection';
import './DepartmentList.css';

const DATA_STRUCTURE = {
  API: 'api',
  MOCK: 'mock', 
  UNKNOWN: 'unknown',
};

const DepartmentList = ({ 
  data, 
  onTeamClick, 
  selectedUnitId,
}) => {
  if (!data) {
    return <EmptyState message="Нет данных для отображения" />;
  }

  const dataStructure = determineDataStructure(data);

  const renderContent = () => {
    switch (dataStructure) {
    case DATA_STRUCTURE.API:
      return (
        <CollapsibleSection 
          data={data}
          level={0}
          onTeamClick={onTeamClick}
          selectedUnitId={selectedUnitId}
        />
      );
    
    case DATA_STRUCTURE.MOCK:
      return data.departments.map(department => (
        <CollapsibleSection 
          key={department.org_unit_id || department.id}
          data={department}
          level={0}
          onTeamClick={onTeamClick}
          selectedUnitId={selectedUnitId}
        />
      ));
    
    case DATA_STRUCTURE.UNKNOWN:
    default:
      return <EmptyState message="Неизвестный формат данных" />;
    }
  };

  return (
    <div className="department-list">
      {renderContent()}
    </div>
  );
};

const determineDataStructure = data => {
  const hasApiStructure = (data.org_unit_id || data.id) && data.name && data.unit_type;
  if (hasApiStructure) {
    return DATA_STRUCTURE.API;
  }

  const hasMockStructure = data.departments && Array.isArray(data.departments);
  if (hasMockStructure) {
    return DATA_STRUCTURE.MOCK;
  }

  return DATA_STRUCTURE.UNKNOWN;
};

const EmptyState = ({ message }) => (
  <div className="department-list--empty">
    {message}
  </div>
);

export default DepartmentList;
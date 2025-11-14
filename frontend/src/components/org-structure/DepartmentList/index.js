import React from 'react';
import CollapsibleSection from '../CollapsibleSection';
import './DepartmentList.css';

const DepartmentList = ({ data, onTeamClick, selectedUnitId }) => {
  if (!data) {
    return <div className="department-list--empty">Нет данных для отображения</div>;
  }

  // Обрабатываем обе структуры данных - из API и моковую
  const renderStructure = () => {
    if ((data.org_unit_id || data.id) && data.name && data.unit_type) {
      return (
        <CollapsibleSection 
          data={data}
          level={0}
          onTeamClick={onTeamClick}
          selectedUnitId={selectedUnitId}
        />
      );
    }
    
    // Если данные из моков (старая структура с departments)
    if (data.departments && Array.isArray(data.departments)) {
      return data.departments.map(department => (
        <CollapsibleSection 
          key={department.org_unit_id || department.id}
          data={department}
          level={0}
          onTeamClick={onTeamClick}
          selectedUnitId={selectedUnitId}
        />
      ));
    }
    
    return <div className="department-list--empty">Неизвестный формат данных</div>;
  };

  return (
    <div className="department-list">
      {renderStructure()}
    </div>
  );
};

export default DepartmentList;
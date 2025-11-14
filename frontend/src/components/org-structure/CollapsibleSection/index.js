import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './CollapsibleSection.css';

const CollapsibleSection = ({ data, level = 0, onTeamClick, selectedUnitId }) => {
  const [isOpen, setIsOpen] = useState(level === 0);
  const navigate = useNavigate();
  
  const hasChildren = data.children && data.children.length > 0;
  
  // Автоматически раскрываем узел, если он выбран из хлебных крошек
  useEffect(() => {
    if (selectedUnitId && hasChildren) {
      // Проверяем, находится ли выбранный узел в этом поддереве
      const isInSubtree = findNodeInSubtree(data, selectedUnitId);
      if (isInSubtree) {
        setIsOpen(true);
      }
    }
  }, [selectedUnitId, data, hasChildren]);

  // Функция для поиска узла в поддереве
  const findNodeInSubtree = (node, targetId) => {
    const nodeId = node.org_unit_id || node.id;
    if (nodeId === targetId) return true;
    if (node.children) {
      for (let child of node.children) {
        if (findNodeInSubtree(child, targetId)) return true;
      }
    }
    return false;
  };

  // Определяем тип элемента на основе unit_type
  const getElementType = () => {
    switch (data.unit_type) {
    case 'group':
    case 'domain':
    case 'legal_entity':
      return 'block';
    case 'department':
      return 'department';
    case 'direction':
      return 'direction';
    default:
      return 'team';
    }
  };

  const elementType = getElementType();
  const isTeam = elementType === 'team';

  // Определяем является ли элемент конечным (без детей)
  const isFinalUnit = !hasChildren;

  // Подсвечиваем выбранный узел
  const isSelected = selectedUnitId === (data.org_unit_id || data.id);

  const handleClick = () => {
    // Если это конечный юнит - переходим на страницу команды
    if (isFinalUnit) {
      const unitId = data.org_unit_id || data.id;
      navigate(`/team/${unitId}`);
      if (onTeamClick) {
        onTeamClick(data);
      }
    } else if (hasChildren) {
      // Для отделов с детьми - раскрытие/скрытие
      setIsOpen(!isOpen);
    }
  };

  const handleTeamClick = (teamData) => {
    const unitId = teamData.org_unit_id || teamData.id;
    navigate(`/team/${unitId}`);
    if (onTeamClick) {
      onTeamClick(teamData);
    }
  };

  return (
    <div className={`collapsible-section collapsible-section--level-${level} ${
      isSelected ? 'collapsible-section--selected' : ''
    }`}
    >
      <div 
        className={`collapsible-section__header ${
          isFinalUnit ? 'collapsible-section__header--team' : ''
        } ${hasChildren || isFinalUnit ? 'collapsible-section__header--clickable' : ''} ${
          isSelected ? 'collapsible-section__header--selected' : ''
        }`}
        onClick={handleClick}
      >
        <div className="collapsible-section__content">
          {hasChildren && !isFinalUnit && (
            <div className="collapsible-section__arrow-left">
              {isOpen ? '▼' : '▶'}
            </div>
          )}
          
          <div className="collapsible-section__info">
            <div className="collapsible-section__name">{data.name}</div>
            {data.unit_type && (
              <div className="collapsible-section__type">
                {data.unit_type}
              </div>
            )}
            {isFinalUnit && (
              <div className="collapsible-section__final-label">
                (команда)
              </div>
            )}
          </div>
        </div>
        
        {isFinalUnit && (
          <div className="collapsible-section__team-arrow">
            👥
          </div>
        )}
      </div>

      {hasChildren && isOpen && (
        <div className="collapsible-section__children">
          {data.children.map(child => (
            <CollapsibleSection 
              key={child.org_unit_id || child.id}
              data={child}
              level={level + 1}
              onTeamClick={handleTeamClick}
              selectedUnitId={selectedUnitId}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default CollapsibleSection;
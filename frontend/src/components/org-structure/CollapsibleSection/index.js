import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { findNodeInSubtree } from '../../../utils/orgStructureUtils';
import './CollapsibleSection.css';

const UNIT_TYPES = {
  GROUP: 'group',
  DOMAIN: 'domain', 
  LEGAL_ENTITY: 'legal_entity',
  DEPARTMENT: 'department',
  DIRECTION: 'direction',
};

const ELEMENT_TYPE_MAP = {
  [UNIT_TYPES.GROUP]: 'block',
  [UNIT_TYPES.DOMAIN]: 'block',
  [UNIT_TYPES.LEGAL_ENTITY]: 'block',
  [UNIT_TYPES.DEPARTMENT]: 'department',
  [UNIT_TYPES.DIRECTION]: 'direction',
};

const CollapsibleSection = ({ 
  data, 
  level = 0, 
  onTeamClick, 
  selectedUnitId,
}) => {
  const [isOpen, setIsOpen] = useState(level === 0);
  const navigate = useNavigate();
  
  const hasChildren = data.children && data.children.length > 0;
  const unitId = data.org_unit_id || data.id;
  const elementType = ELEMENT_TYPE_MAP[data.unit_type] || 'team';
  const isTeam = elementType === 'team';
  const isFinalUnit = !hasChildren;
  const isSelected = selectedUnitId === unitId;

  useEffect(() => {
    if (selectedUnitId && hasChildren) {
      const shouldOpen = findNodeInSubtree(data, selectedUnitId);
      if (shouldOpen) {
        setIsOpen(true);
      }
    }
  }, [selectedUnitId, data, hasChildren]);

  const handleHeaderClick = () => {
    if (isFinalUnit) {
      navigateToTeam(data);
    } else if (hasChildren) {
      setIsOpen(prev => !prev);
    }
  };

  const navigateToTeam = teamData => {
    const teamId = teamData.org_unit_id || teamData.id;
    navigate(`/team/${teamId}`);
    onTeamClick?.(teamData);
  };

  return (
    <div className={getContainerClassName(level, isSelected)}>
      <SectionHeader
        data={data}
        hasChildren={hasChildren}
        isFinalUnit={isFinalUnit}
        isOpen={isOpen}
        isSelected={isSelected}
        onClick={handleHeaderClick}
      />
      
      {hasChildren && isOpen && (
        <SectionChildren
          data={data}
          level={level}
          onTeamClick={navigateToTeam}
          selectedUnitId={selectedUnitId}
        />
      )}
    </div>
  );
};

const getContainerClassName = (level, isSelected) => {
  const baseClass = `collapsible-section collapsible-section--level-${level}`;
  return isSelected ? `${baseClass} collapsible-section--selected` : baseClass;
};

const SectionHeader = ({ 
  data, 
  hasChildren, 
  isFinalUnit, 
  isOpen, 
  isSelected, 
  onClick,
}) => {
  const isClickable = hasChildren || isFinalUnit;

  return (
    <div 
      className={getHeaderClassName(isFinalUnit, isClickable, isSelected)}
      onClick={isClickable ? onClick : undefined}
    >
      <div className="collapsible-section__content">
        {hasChildren && !isFinalUnit && (
          <SectionArrow isOpen={isOpen} />
        )}
        
        <SectionInfo 
          data={data} 
          isFinalUnit={isFinalUnit} 
        />
      </div>
      
      {isFinalUnit && <TeamIndicator />}
    </div>
  );
};

const getHeaderClassName = (isFinalUnit, isClickable, isSelected) => {
  const baseClass = 'collapsible-section__header';
  const modifiers = [
    isFinalUnit && 'collapsible-section__header--team',
    isClickable && 'collapsible-section__header--clickable', 
    isSelected && 'collapsible-section__header--selected',
  ].filter(Boolean).join(' ');

  return `${baseClass} ${modifiers}`;
};

const SectionArrow = ({ isOpen }) => (
  <div className="collapsible-section__arrow-left">
    {isOpen ? '▼' : '▶'}
  </div>
);

const SectionInfo = ({ data, isFinalUnit }) => (
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
);

const TeamIndicator = () => (
  <div className="collapsible-section__team-arrow">
    👥
  </div>
);

const SectionChildren = ({ data, level, onTeamClick, selectedUnitId }) => (
  <div className="collapsible-section__children">
    {data.children.map(child => (
      <CollapsibleSection 
        key={child.org_unit_id || child.id}
        data={child}
        level={level + 1}
        onTeamClick={onTeamClick}
        selectedUnitId={selectedUnitId}
      />
    ))}
  </div>
);

export default CollapsibleSection;
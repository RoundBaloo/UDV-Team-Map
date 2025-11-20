import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getEmployeesByUnitId, getManagerByUnitId, getMembersByUnitId } from '../utils/mockData';
import { findPathToNode } from '../utils/helpers';

const findOrgUnitById = (node, unitId) => {
  const nodeId = node.org_unit_id || node.id;
  
  if (nodeId === unitId) {
    return node;
  }
  
  if (node.children && node.children.length > 0) {
    for (let child of node.children) {
      const found = findOrgUnitById(child, unitId);
      if (found) return found;
    }
  }
  
  return null;
};

export const useTeam = () => {
  const { id } = useParams();
  const [state, setState] = useState({
    team: null,
    loading: true,
    manager: null,
    members: [],
    breadcrumbPath: [],
  });

  useEffect(() => {
    const loadTeamData = async () => {
      try {
        setState(prev => ({ ...prev, loading: true }));
        const unitId = parseInt(id);
        
        let orgStructure = null;
        let teamNode = null;
        
        try {
          const { orgUnitsApi } = await import('../services/api/orgUnits');
          orgStructure = await orgUnitsApi.getOrgStructure();
          teamNode = findOrgUnitById(orgStructure, unitId);
          
          if (orgStructure) {
            const path = findPathToNode(orgStructure, unitId);
            if (path) {
              const filteredPath = path.filter(item => (item.org_unit_id || item.id) !== 1);
              setState(prev => ({ ...prev, breadcrumbPath: filteredPath }));
            }
          }
        } catch (apiError) {
          const { mockOrgStructure } = await import('../utils/mockData');
          orgStructure = mockOrgStructure;
          teamNode = findOrgUnitById(mockOrgStructure, unitId);
          
          if (mockOrgStructure) {
            const path = findPathToNode(mockOrgStructure, unitId);
            if (path) {
              const filteredPath = path.filter(item => (item.org_unit_id || item.id) !== 1);
              setState(prev => ({ ...prev, breadcrumbPath: filteredPath }));
            }
          }
        }

        if (teamNode) {
          const allEmployees = getEmployeesByUnitId(unitId);
          const teamManager = getManagerByUnitId(unitId);
          const teamMembers = getMembersByUnitId(unitId);

          setState(prev => ({
            ...prev,
            team: {
              id: teamNode.org_unit_id || teamNode.id,
              name: teamNode.name,
              description: teamNode.description || `Команда ${teamNode.name}`,
              employee_count: allEmployees.length,
            },
            manager: teamManager,
            members: teamMembers,
          }));
        } else {
          const allEmployees = getEmployeesByUnitId(unitId);
          const teamManager = getManagerByUnitId(unitId);
          const teamMembers = getMembersByUnitId(unitId);
          
          if (allEmployees.length > 0) {
            setState(prev => ({
              ...prev,
              team: {
                id: unitId,
                name: `Команда #${unitId}`,
                description: 'Команда сотрудников',
                employee_count: allEmployees.length,
              },
              manager: teamManager,
              members: teamMembers,
            }));
          }
        }
      } catch (error) {
        console.error('Error loading team data:', error);
      } finally {
        setState(prev => ({ ...prev, loading: false }));
      }
    };

    loadTeamData();
  }, [id]);

  return state;
};
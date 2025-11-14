import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import Breadcrumbs from '../../components/common/Breadcrumbs';
import { getEmployeesByUnitId, getManagerByUnitId, getMembersByUnitId } from '../../utils/mockData';
import { findPathToNode } from '../../utils/helpers';
import './TeamPage.css';

// Функция для поиска подразделения в структуре с бэкенда
const findOrgUnitById = (node, unitId) => {
  const nodeId = node.org_unit_id || node.id;
  console.log('Searching in node:', nodeId, node.name, 'for:', unitId);
  
  if (nodeId === unitId) {
    console.log('Found node:', node);
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

const TeamPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [manager, setManager] = useState(null);
  const [members, setMembers] = useState([]);
  const [breadcrumbPath, setBreadcrumbPath] = useState([]);

  useEffect(() => {
    const loadTeamData = async () => {
      try {
        setLoading(true);
        const unitId = parseInt(id);
        console.log('Loading team data for unit ID:', unitId);
        
        // Пробуем загрузить структуру с бэкенда
        let orgStructure = null;
        let teamNode = null;
        try {
          const { orgUnitsApi } = await import('../../services/api/orgUnits');
          orgStructure = await orgUnitsApi.getOrgStructure();
          console.log('Org structure from API:', orgStructure);
          teamNode = findOrgUnitById(orgStructure, unitId);
          
          // Находим путь для хлебных крошек
          if (orgStructure) {
            const path = findPathToNode(orgStructure, unitId);
            if (path) {
              // Убираем корневой элемент (UDV Group) из пути, так как у нас уже есть "Главная"
              const filteredPath = path.filter(item => (item.org_unit_id || item.id) !== 1);
              setBreadcrumbPath(filteredPath);
            }
          }
        } catch (apiError) {
          console.log('API not available, using mock structure');
          // Если API недоступно, используем моковую структуру
          const { mockOrgStructure } = await import('../../utils/mockData');
          orgStructure = mockOrgStructure;
          teamNode = findOrgUnitById(mockOrgStructure, unitId);
          
          // Находим путь для хлебных крошек из моковых данных
          if (mockOrgStructure) {
            const path = findPathToNode(mockOrgStructure, unitId);
            if (path) {
              // Убираем корневой элемент (UDV Group) из пути
              const filteredPath = path.filter(item => (item.org_unit_id || item.id) !== 1);
              setBreadcrumbPath(filteredPath);
            }
          }
        }

        console.log('Found team node:', teamNode);

        if (teamNode) {
          // Получаем сотрудников из моков
          const allEmployees = getEmployeesByUnitId(unitId);
          const teamManager = getManagerByUnitId(unitId);
          const teamMembers = getMembersByUnitId(unitId);

          console.log('Employees data for unit', unitId, ':', {
            allEmployees,
            teamManager,
            teamMembers,
          });

          setTeam({
            id: teamNode.org_unit_id || teamNode.id,
            name: teamNode.name,
            description: teamNode.description || `Команда ${teamNode.name}`,
            employee_count: allEmployees.length,
          });
          setManager(teamManager);
          setMembers(teamMembers);
        } else {
          console.error('Team node not found for ID:', unitId);
          // Создаем базовую информацию о команде даже если не нашли в структуре
          const allEmployees = getEmployeesByUnitId(unitId);
          const teamManager = getManagerByUnitId(unitId);
          const teamMembers = getMembersByUnitId(unitId);
          
          if (allEmployees.length > 0) {
            setTeam({
              id: unitId,
              name: `Команда #${unitId}`,
              description: 'Команда сотрудников',
              employee_count: allEmployees.length,
            });
            setManager(teamManager);
            setMembers(teamMembers);
          }
        }
      } catch (error) {
        console.error('Error loading team data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTeamData();
  }, [id]);

  // Обработчик клика по сотруднику
  const handleEmployeeClick = (employeeId) => {
    navigate(`/profile/${employeeId}`);
  };

  // Обработчик клика по руководителю
  const handleManagerClick = (managerId) => {
    navigate(`/profile/${managerId}`);
  };

  if (loading) {
    return (
      <div className="team-page">
        <Header />
        {/* <Breadcrumbs customPath={breadcrumbPath} /> */}
        <main className="team-main">
          <div className="container">
            <div className="loading-placeholder">Загрузка информации о команде...</div>
          </div>
        </main>
      </div>
    );
  }

  if (!team) {
    return (
      <div className="team-page">
        <Header />
        {/* <Breadcrumbs customPath={breadcrumbPath} /> */}
        <main className="team-main">
          <div className="container">
            <div className="error-placeholder">Команда не найдена</div>
          </div>
        </main>
      </div>
    );
  }

  // Безопасное получение инициалов
  const getInitials = (employee) => {
    if (!employee) return '??';
    return `${employee.first_name?.[0] || ''}${employee.last_name?.[0] || ''}`;
  };

  // Безопасное получение полного имени
  const getFullName = (employee) => {
    if (!employee) return 'Неизвестный сотрудник';
    return `${employee.first_name || ''} ${employee.last_name || ''}`.trim();
  };

  return (
    <div className="team-page">
      <Header />
      {/* <Breadcrumbs customPath={breadcrumbPath} /> */}
      
      <main className="team-main">
        <div className="container">
          <div className="team-header">
            <h1>{team.name}</h1>
            <div className="team-stats">
              Участников: {team.employee_count}
            </div>
          </div>

          <div className="team-description">
            <p>{team.description}</p>
          </div>

          {manager && (
            <div className="team-section">
              <h2>Руководитель</h2>
              <div 
                className="manager-card clickable-card"
                onClick={() => handleManagerClick(manager.employee_id || manager.id)}
              >
                <div className="manager-avatar">
                  {manager.photo ? (
                    <img src={manager.photo} alt={getFullName(manager)} />
                  ) : (
                    <div className="avatar-placeholder">
                      {getInitials(manager)}
                    </div>
                  )}
                </div>
                <div className="manager-info">
                  <div className="manager-name">
                    {getFullName(manager)}
                  </div>
                  <div className="manager-title">{manager.title || 'Должность не указана'}</div>
                  <div className="manager-contact">
                    {manager.email || 'Email не указан'} • {manager.work_phone || 'Телефон не указан'}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="team-section">
            <h2>Участники команды ({members.length})</h2>
            <div className="members-grid">
              {members.map(member => (
                <div 
                  key={member.employee_id || member.id} 
                  className="member-card clickable-card"
                  onClick={() => handleEmployeeClick(member.employee_id || member.id)}
                >
                  <div className="member-avatar">
                    {member.photo ? (
                      <img src={member.photo} alt={getFullName(member)} />
                    ) : (
                      <div className="avatar-placeholder">
                        {getInitials(member)}
                      </div>
                    )}
                  </div>
                  <div className="member-info">
                    <div className="member-name">
                      {getFullName(member)}
                    </div>
                    <div className="member-title">{member.title || 'Должность не указана'}</div>
                    <div className="member-contact">
                      {member.email || 'Email не указан'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default TeamPage;
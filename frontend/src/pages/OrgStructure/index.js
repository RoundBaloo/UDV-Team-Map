import React, { useState, useEffect } from 'react';
import Header from '../../components/common/Header';
import Breadcrumbs from '../../components/common/Breadcrumbs';
import DepartmentList from '../../components/org-structure/DepartmentList';
import { orgUnitsApi } from '../../services/api/orgUnits';
import { mockOrgStructure } from '../../utils/mockData';
import './OrgStructure.css';

const OrgStructure = () => {
  const [orgData, setOrgData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedUnitId, setSelectedUnitId] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  // Проверяем выбранный узел из хлебных крошек
  useEffect(() => {
    const checkSelectedUnit = () => {
      try {
        const savedUnit = sessionStorage.getItem('selectedOrgUnit');
        if (savedUnit) {
          const unit = JSON.parse(savedUnit);
          setSelectedUnitId(unit.org_unit_id || unit.id);
          // Очищаем storage после использования
          sessionStorage.removeItem('selectedOrgUnit');
        }
      } catch (error) {
        console.error('Error processing selected unit:', error);
      }
    };

    if (!loading && orgData) {
      checkSelectedUnit();
    }
  }, [loading, orgData]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Пробуем загрузить данные с бэкенда
      const data = await orgUnitsApi.getOrgStructure();
      console.log('Org structure from API:', data);
      setOrgData(data);
      
    } catch (err) {
      console.error('Error loading org structure from API:', err);
      setError('Не удалось загрузить структуру из базы данных');
      
      // Используем моки как fallback
      console.log('Using mock data as fallback');
      setOrgData(mockOrgStructure);
    } finally {
      setLoading(false);
    }
  };

  const handleTeamClick = (teamData) => {
    console.log('Team clicked:', teamData);
    // Логика обработки клика по команде
  };

  // Функция для передачи выбранного узла в DepartmentList
  const getEnhancedOrgData = () => {
    if (!orgData) return null;
    
    // Добавляем информацию о выбранном узле к данным
    return {
      ...orgData,
      _selectedUnitId: selectedUnitId,
    };
  };

  if (loading) {
    return (
      <div className="org-structure-page">
        <Header />
        {/* <Breadcrumbs /> */}
        <main className="org-structure-main">
          <div className="container">
            <div className="loading-placeholder">
              Загрузка организационной структуры...
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="org-structure-page">
      <Header />
      {/* <Breadcrumbs /> */}
      
      <main className="org-structure-main">
        <div className="container">
          <div className="org-structure-header">
            <h1>Организационная структура</h1>
            {error && (
              <div className="alert alert-warning">
                {error}
                <button 
                  className="btn btn-secondary btn-sm"
                  onClick={loadData}
                  style={{ marginLeft: '10px' }}
                >
                  Повторить
                </button>
              </div>
            )}
          </div>
          
          <div className="card">
            <DepartmentList 
              data={getEnhancedOrgData()} 
              onTeamClick={handleTeamClick}
              selectedUnitId={selectedUnitId}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default OrgStructure;
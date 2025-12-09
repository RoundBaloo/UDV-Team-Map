import React, { useState, useEffect } from 'react';
import Header from '../../components/common/Header';
import DepartmentList from '../../components/org-structure/DepartmentList';
import { orgUnitsApi } from '../../services/api/orgUnits';
import { mockOrgStructure } from '../../utils/mockData';
import { findPathToNode } from '../../utils/helpers';
import './OrgStructure.css';

const STORAGE_KEYS = {
  SELECTED_UNIT: 'selectedOrgUnit',
};

const OrgStructure = () => {
  const [state, setState] = useState({
    orgData: null,
    loading: true,
    error: null,
    selectedUnitId: null,
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (!state.loading && state.orgData) {
      checkSelectedUnit();
    }
  }, [state.loading, state.orgData]);

  const loadData = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const data = await orgUnitsApi.getOrgStructure();
      console.log('Org structure from API:', data);
      setState(prev => ({ ...prev, orgData: data }));
      
    } catch (err) {
      console.error('Error loading org structure from API:', err);
      
      setState(prev => ({ 
        ...prev, 
        error: 'Не удалось загрузить структуру из базы данных',
        orgData: mockOrgStructure,
      }));
      console.log('Using mock data as fallback');
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  const checkSelectedUnit = () => {
    try {
      const savedUnit = sessionStorage.getItem(STORAGE_KEYS.SELECTED_UNIT);
      if (savedUnit) {
        const unit = JSON.parse(savedUnit);
        setState(prev => ({ 
          ...prev, 
          selectedUnitId: unit.org_unit_id || unit.id,
        }));
        sessionStorage.removeItem(STORAGE_KEYS.SELECTED_UNIT);
      }
    } catch (error) {
      console.error('Error processing selected unit:', error);
    }
  };

  const handleTeamClick = teamData => {
    console.log('Team clicked:', teamData);
  };

  const handleRetry = () => {
    loadData();
  };

  if (state.loading) {
    return <LoadingState />;
  }

  return (
    <div className="org-structure-page">
      <Header />
      
      <main className="org-structure-main">
        <div className="container">
          <OrgStructureHeader 
            error={state.error}
            onRetry={handleRetry}
          />
          
          <div className="card">
            <DepartmentList 
              data={state.orgData} 
              onTeamClick={handleTeamClick}
              selectedUnitId={state.selectedUnitId}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

const LoadingState = () => (
  <div className="org-structure-page">
    <Header />
    <main className="org-structure-main">
      <div className="container">
        <div className="loading-placeholder">
          Загрузка организационной структуры...
        </div>
      </div>
    </main>
  </div>
);

const OrgStructureHeader = ({ error, onRetry }) => (
  <div className="org-structure-header">
    <h1>Оргструктура UDV Group</h1>
    {error && (
      <div className="alert alert-warning">
        {error}
        <button 
          className="btn btn-secondary btn-sm"
          onClick={onRetry}
          style={{ marginLeft: '10px' }}
        >
          Повторить
        </button>
      </div>
    )}
  </div>
);

export default OrgStructure;
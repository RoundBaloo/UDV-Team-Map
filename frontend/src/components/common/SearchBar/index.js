import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { debounce } from '../../../utils/helpers';
import { employeesApi } from '../../../services/api/employees';
import { orgUnitsApi } from '../../../services/api/orgUnits';
import './SearchBar.css';

const DEBOUNCE_DELAY = 300;
const BLUR_DELAY = 200;

const DEFAULT_TEXTS = {
  placeholder: 'Поиск сотрудников или отделов...',
  loading: 'Поиск...',
  noResults: 'Ничего не найдено',
  noDepartment: 'Не указан',
  noTitle: 'Должность не указана',
};

const SearchBar = () => {
  const [searchState, setSearchState] = useState({
    query: '',
    suggestions: [],
    showSuggestions: false,
    loading: false,
    searchType: 'employees',
  });
  
  const navigate = useNavigate();

  const performSearch = useCallback(async (searchQuery, searchType) => {
    if (!searchQuery.trim()) {
      setSearchState(prev => ({ ...prev, suggestions: [] }));
      return;
    }

    setSearchState(prev => ({ ...prev, loading: true }));

    try {
      let suggestions = [];
      
      if (searchType === 'employees') {
        const employeesResponse = await employeesApi.getEmployees({ q: searchQuery });
        
        suggestions = employeesResponse.map(emp => ({
          id: emp.employee_id,
          type: 'employee',
          name: `${emp.first_name} ${emp.last_name}`,
          title: emp.title,
          department: emp.org_unit?.name || DEFAULT_TEXTS.noDepartment,
        }));
      } else if (searchType === 'orgUnits') {
        const orgUnitsResponse = await orgUnitsApi.searchOrgUnits({ q: searchQuery });
        
        suggestions = orgUnitsResponse.map(unit => ({
          id: unit.org_unit_id,
          type: 'orgUnit',
          name: unit.name,
          unit_type: unit.unit_type,
          path: unit.path || [],
        }));
      }

      setSearchState(prev => ({ 
        ...prev, 
        suggestions,
        loading: false,
      }));
      
    } catch (error) {
      console.error('Search error:', error);
      setSearchState(prev => ({ 
        ...prev, 
        suggestions: [],
        loading: false,
      }));
    }
  }, []);

  const debouncedSearch = useCallback(
    debounce((searchQuery, searchType) => performSearch(searchQuery, searchType), DEBOUNCE_DELAY),
    [performSearch],
  );

  const handleInputChange = e => {
    const value = e.target.value;
    const hasQuery = value.trim().length > 0;
    
    setSearchState(prev => ({ 
      ...prev, 
      query: value,
      showSuggestions: hasQuery,
    }));
    
    if (hasQuery) {
      debouncedSearch(value, searchState.searchType);
    } else {
      setSearchState(prev => ({ ...prev, suggestions: [] }));
    }
  };

  const handleSearchTypeChange = (type) => {
    setSearchState(prev => {
      const newState = { 
        ...prev, 
        searchType: type,
        suggestions: [],
      };
      
      if (prev.query.trim()) {
        debouncedSearch(prev.query, type);
      }
      
      return newState;
    });
  };

  const handleSuggestionClick = item => {
    setSearchState({
      query: '',
      suggestions: [],
      showSuggestions: false,
      loading: false,
      searchType: searchState.searchType,
    });

    if (item.type === 'employee') {
      navigate(`/profile/${item.id}`);
    } else if (item.type === 'orgUnit') {
      // Сохраняем выбранную орг.единицу
      sessionStorage.setItem('selectedOrgUnit', JSON.stringify({
        org_unit_id: item.id,
        name: item.name,
        unit_type: item.unit_type,
        path: item.path,
      }));
      
      // Убираем хлебные крошки из sessionStorage, если они есть
      sessionStorage.removeItem('breadcrumbPath');
      
      navigate('/structure');
    }
  };

  const handleInputFocus = () => {
    const { query, suggestions } = searchState;
    if (query && suggestions.length > 0) {
      setSearchState(prev => ({ ...prev, showSuggestions: true }));
    }
  };

  const handleInputBlur = () => {
    setTimeout(() => {
      setSearchState(prev => ({ ...prev, showSuggestions: false }));
    }, BLUR_DELAY);
  };

  const handleKeyDown = e => {
    const { query, suggestions } = searchState;
    if (e.key === 'Enter' && query.trim() && suggestions.length > 0) {
      handleSuggestionClick(suggestions[0]);
    }
  };

  const formatBreadcrumbPath = (path) => {
    if (!path || !Array.isArray(path)) return '';
    
    // Исключаем саму найденную единицу из хлебных крошек
    const filteredPath = path.filter(item => 
      item.unit_type !== 'department' && 
      item.unit_type !== 'direction' &&
      item.unit_type !== 'team'
    );
    
    return filteredPath.map(item => item.name).join(' - ');
  };

  const { query, suggestions, showSuggestions, loading, searchType } = searchState;

  return (
    <div className="search-bar">
      <div className="search-bar__switcher">
        <button
          type="button"
          className={`search-bar__switch-btn ${searchType === 'employees' ? 'active' : ''}`}
          onClick={() => handleSearchTypeChange('employees')}
        >
          Сотрудники
        </button>
        <button
          type="button"
          className={`search-bar__switch-btn ${searchType === 'orgUnits' ? 'active' : ''}`}
          onClick={() => handleSearchTypeChange('orgUnits')}
        >
          Орг.единицы
        </button>
      </div>
      
      <div className="search-bar__input-container">
        <input
          type="text"
          className="search-bar__input"
          placeholder={searchType === 'employees' ? 'Поиск сотрудников...' : 'Поиск отделов...'}
          value={query}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
        />
        <div className="search-bar__icon">🔍</div>
      </div>
      
      {showSuggestions && (
        <div className="search-bar__suggestions">
          {loading && (
            <div className="search-bar__suggestion search-bar__suggestion--loading">
              {DEFAULT_TEXTS.loading}
            </div>
          )}
          
          {!loading && suggestions.map(item => (
            <div
              key={`${item.type}-${item.id}`}
              className="search-bar__suggestion"
              onClick={() => handleSuggestionClick(item)}
            >
              <div className="search-bar__suggestion-info">
                <div className="search-bar__suggestion-name">{item.name}</div>
                
                {item.type === 'employee' ? (
                  <>
                    <div className="search-bar__suggestion-title">
                      {item.title || DEFAULT_TEXTS.noTitle}
                    </div>
                    {item.department && (
                      <div className="search-bar__suggestion-department">
                        {item.department}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="search-bar__suggestion-type">
                      {item.unit_type}
                    </div>
                    {item.path && item.path.length > 0 && (
                      <div className="search-bar__suggestion-path">
                        {formatBreadcrumbPath(item.path)}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
          
          {!loading && query && suggestions.length === 0 && (
            <div className="search-bar__suggestion search-bar__suggestion--empty">
              {DEFAULT_TEXTS.noResults}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
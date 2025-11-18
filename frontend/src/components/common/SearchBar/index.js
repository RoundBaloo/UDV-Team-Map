import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { debounce } from '../../../utils/helpers';
import { employeesApi } from '../../../services/api/employees';
import './SearchBar.css';

const DEBOUNCE_DELAY = 300;
const BLUR_DELAY = 200;

const DEFAULT_TEXTS = {
  placeholder: 'Поиск сотрудников...',
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
  });
  
  const navigate = useNavigate();

  const performSearch = useCallback(async searchQuery => {
    if (!searchQuery.trim()) {
      setSearchState(prev => ({ ...prev, suggestions: [] }));
      return;
    }

    setSearchState(prev => ({ ...prev, loading: true }));

    try {
      const employeesResponse = await employeesApi.getEmployees({ q: searchQuery });
      
      const employeeSuggestions = employeesResponse.map(emp => ({
        id: emp.employee_id,
        type: 'employee',
        name: `${emp.first_name} ${emp.last_name}`,
        title: emp.title,
        department: emp.org_unit?.name || DEFAULT_TEXTS.noDepartment,
      }));

      setSearchState(prev => ({ 
        ...prev, 
        suggestions: employeeSuggestions,
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
    debounce((searchQuery) => performSearch(searchQuery), DEBOUNCE_DELAY),
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
      debouncedSearch(value);
    } else {
      setSearchState(prev => ({ ...prev, suggestions: [] }));
    }
  };

  const handleSuggestionClick = item => {
    setSearchState({
      query: '',
      suggestions: [],
      showSuggestions: false,
      loading: false,
    });

    if (item.type === 'employee') {
      navigate(`/profile/${item.id}`);
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

  const { query, suggestions, showSuggestions, loading } = searchState;

  return (
    <div className="search-bar">
      <SearchInput
        query={query}
        onChange={handleInputChange}
        onFocus={handleInputFocus}
        onBlur={handleInputBlur}
        onKeyDown={handleKeyDown}
        placeholder={DEFAULT_TEXTS.placeholder}
      />
      
      {showSuggestions && (
        <SearchSuggestions
          suggestions={suggestions}
          loading={loading}
          query={query}
          onSuggestionClick={handleSuggestionClick}
        />
      )}
    </div>
  );
};

const SearchInput = ({ query, onChange, onFocus, onBlur, onKeyDown, placeholder }) => {
  return (
    <div className="search-bar__input-container">
      <input
        type="text"
        className="search-bar__input"
        placeholder={placeholder}
        value={query}
        onChange={onChange}
        onFocus={onFocus}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
      />
      <div className="search-bar__icon" />
    </div>
  );
};

const SearchSuggestions = ({ suggestions, loading, query, onSuggestionClick }) => {
  return (
    <div className="search-bar__suggestions">
      {loading && <LoadingSuggestion />}
      
      {!loading && suggestions.map(item => (
        <SuggestionItem
          key={`${item.type}-${item.id}`}
          item={item}
          onClick={onSuggestionClick}
        />
      ))}
      
      {!loading && query && suggestions.length === 0 && (
        <EmptySuggestion />
      )}
    </div>
  );
};

const LoadingSuggestion = () => (
  <div className="search-bar__suggestion search-bar__suggestion--loading">
    {DEFAULT_TEXTS.loading}
  </div>
);

const EmptySuggestion = () => (
  <div className="search-bar__suggestion search-bar__suggestion--empty">
    {DEFAULT_TEXTS.noResults}
  </div>
);

const SuggestionItem = ({ item, onClick }) => {
  return (
    <div
      className="search-bar__suggestion"
      onClick={() => onClick(item)}
    >
      <span className="search-bar__suggestion-icon">👤</span>
      <div className="search-bar__suggestion-info">
        <div className="search-bar__suggestion-name">{item.name}</div>
        <div className="search-bar__suggestion-title">
          {item.title || DEFAULT_TEXTS.noTitle}
        </div>
      </div>
    </div>
  );
};

export default SearchBar;
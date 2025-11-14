import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { debounce } from '../../../utils/helpers';
import { employeesApi } from '../../../services/api/employees';
import './SearchBar.css';

const SearchBar = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const searchItems = useCallback(
    debounce(async (searchQuery) => {
      if (!searchQuery.trim()) {
        setSuggestions([]);
        return;
      }

      setLoading(true);

      try {
        // Реальный поиск по сотрудникам через API
        const employeesResponse = await employeesApi.getEmployees({ q: searchQuery });
        
        const employeeSuggestions = employeesResponse.map(emp => ({
          id: emp.employee_id,
          type: 'employee',
          name: `${emp.first_name} ${emp.last_name}`,
          title: emp.title,
          department: emp.org_unit?.name || 'Не указан',
        }));

        setSuggestions(employeeSuggestions);
        
      } catch (error) {
        console.error('Search error:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    
    if (value.trim()) {
      searchItems(value);
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (item) => {
    setQuery('');
    setShowSuggestions(false);
    setSuggestions([]);

    if (item.type === 'employee') {
      navigate(`/profile/${item.id}`);
    }
  };

  const handleInputFocus = () => {
    if (query && suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleInputBlur = () => {
    setTimeout(() => setShowSuggestions(false), 200);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && query.trim() && suggestions.length > 0) {
      handleSuggestionClick(suggestions[0]);
    }
  };

  return (
    <div className="search-bar">
      <div className="search-bar__input-container">
        <input
          type="text"
          className="search-bar__input"
          placeholder="Поиск сотрудников..."
          value={query}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
        />
        <div className="search-bar__icon" />
      </div>

      {showSuggestions && (
        <div className="search-bar__suggestions">
          {loading && (
            <div className="search-bar__suggestion search-bar__suggestion--loading">
              Поиск...
            </div>
          )}
          
          {!loading && suggestions.map(item => (
            <div
              key={`${item.type}-${item.id}`}
              className="search-bar__suggestion"
              onClick={() => handleSuggestionClick(item)}
            >
              <span className="search-bar__suggestion-icon">
                👤
              </span>
              <div className="search-bar__suggestion-info">
                <div className="search-bar__suggestion-name">{item.name}</div>
                <div className="search-bar__suggestion-title">
                  {item.title || 'Должность не указана'}
                </div>
              </div>
            </div>
          ))}
          
          {!loading && query && suggestions.length === 0 && (
            <div className="search-bar__suggestion search-bar__suggestion--empty">
              Ничего не найдено
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
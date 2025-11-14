import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../services/auth/useAuth';
import { formatEmployeeName } from '../../../utils/helpers';
import SearchBar from '../SearchBar';
import './Header.css';

const Header = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [isAdminPanelVisible, setIsAdminPanelVisible] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleProfileClick = () => {
    navigate('/profile');
  };

  const toggleAdminPanel = () => {
    setIsAdminPanelVisible(!isAdminPanelVisible);
  };

  return (
    <header className="header">
      <div className="header__container">
        {/* Первая строка */}
        <div className="header__top">
          <div className="header__left">
            <Link to="/" className="header__logo">
              UDV Team Map
            </Link>
            <SearchBar />
          </div>

          <label className="header__admin-toggle">
            <input 
              type="checkbox"
              checked={isAdminPanelVisible}
              onChange={toggleAdminPanel}
              className="header__admin-checkbox"
            />
            <span className="header__admin-toggle-text">
              Административная панель
            </span>
          </label>

          <div className="header__right">
            {user && (
              <div className="header__user">
                <button 
                  className="header__profile-btn"
                  onClick={handleProfileClick}
                  title="Мой профиль"
                >
                  <div className="header__user-avatar">
                    {user.first_name?.[0]}{user.last_name?.[0]}
                  </div>
                  <span className="header__user-name">
                    {formatEmployeeName(user.first_name, user.last_name)}
                  </span>
                </button>
                
                <button 
                  className="header__logout-btn"
                  onClick={handleLogout}
                  title="Выйти"
                >
                  Выйти
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Вторая строка - только для админов */}
        {isAdmin && (
          <div className="header__bottom">
            <div className="header__admin-controls">

              {isAdminPanelVisible && (
                <nav className="header__admin-nav">
                  <Link to="/admin/users" className="header__admin-nav-link">
                    Пользователи
                  </Link>
                  <Link to="/admin/photos" className="header__admin-nav-link">
                    Модерация фото
                  </Link>
                </nav>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
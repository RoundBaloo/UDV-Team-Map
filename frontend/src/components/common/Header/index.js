import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../services/auth/useAuth';
import { formatEmployeeName } from '../../../utils/helpers';
import SearchBar from '../SearchBar';
import './Header.css';

const ADMIN_ROUTES = {
  USERS: '/admin/users',
  PHOTOS: '/admin/photos',
  SYNC: '/admin/sync',
};

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
    setIsAdminPanelVisible(prev => !prev);
  };

  return (
    <header className="header">
      <div className="header__container">
        <HeaderTop 
          user={user}
          isAdmin={isAdmin}
          isAdminPanelVisible={isAdminPanelVisible}
          onProfileClick={handleProfileClick}
          onLogout={handleLogout}
          onToggleAdminPanel={toggleAdminPanel}
        />
        
        {isAdmin && (
          <HeaderBottom 
            isAdminPanelVisible={isAdminPanelVisible}
          />
        )}
      </div>
    </header>
  );
};

const HeaderTop = ({ 
  user, 
  isAdmin, 
  isAdminPanelVisible, 
  onProfileClick, 
  onLogout, 
  onToggleAdminPanel,
}) => {
  return (
    <div className="header__top">
      <div className="header__left">
        <Link to="/" className="header__logo">
          UDV Team Map
        </Link>
        <SearchBar />
      </div>

      {isAdmin && (
        <AdminToggle 
          isVisible={isAdminPanelVisible}
          onToggle={onToggleAdminPanel}
        />
      )}

      {user && (
        <UserMenu 
          user={user}
          onProfileClick={onProfileClick}
          onLogout={onLogout}
        />
      )}
    </div>
  );
};

const AdminToggle = ({ isVisible, onToggle }) => {
  return (
    <label className="header__admin-toggle">
      <input 
        type="checkbox"
        checked={isVisible}
        onChange={onToggle}
        className="header__admin-checkbox"
      />
      <span className="header__admin-toggle-text">
        Административная панель
      </span>
    </label>
  );
};

const UserMenu = ({ user, onProfileClick, onLogout }) => {
  return (
    <div className="header__right">
      <div className="header__user">
        <button 
          className="header__profile-btn"
          onClick={onProfileClick}
          title="Мой профиль"
        >
          <div className="header__user-avatar">
            {user.first_name?.[0]}{user.last_name?.[0]}
          </div>
          {/* <span className="header__user-name">
            {formatEmployeeName(user.first_name, user.last_name)}
          </span> */}
        </button>
        
        <button 
          className="header__logout-btn"
          onClick={onLogout}
          title="Выйти"
        >
          Выйти
        </button>
      </div>
    </div>
  );
};

const HeaderBottom = ({ isAdminPanelVisible }) => {
  if (!isAdminPanelVisible) {
    return null;
  }

  return (
    <div className="header__bottom">
      <div className="header__admin-controls">
        <nav className="header__admin-nav">
          <Link to={ADMIN_ROUTES.USERS} className="header__admin-nav-link">
            Пользователи
          </Link>
          <Link to={ADMIN_ROUTES.PHOTOS} className="header__admin-nav-link">
            Модерация фото
          </Link>
          <Link to={ADMIN_ROUTES.SYNC} className="header__admin-nav-link">
            Синхронизация
          </Link>
        </nav>
      </div>
    </div>
  );
};

export default Header;
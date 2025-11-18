import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Breadcrumbs.css';

const BREADCRUMB_MAP = {
  '': 'Главная',
  'admin': 'Админка', 
  'users': 'Пользователи',
  'photos': 'Фотографии',
  'profile': 'Профиль',
  'team': 'Команда',
};

const Breadcrumbs = ({ customPath }) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const handleOrgUnitClick = (item, event) => {
    event.preventDefault();
    
    sessionStorage.setItem('selectedOrgUnit', JSON.stringify({
      id: item.id,
      name: item.name,
      unit_type: item.unit_type,
    }));
    
    navigate('/');
  };

  const renderBreadcrumbItem = (item, isLast, isCustomPath = false) => {
    const content = isLast ? (
      <span className="breadcrumbs__current">{item.name}</span>
    ) : isCustomPath ? (
      <a 
        href="/"
        className="breadcrumbs__item"
        onClick={(e) => handleOrgUnitClick(item, e)}
      >
        {item.name}
      </a>
    ) : (
      <Link to={item.routeTo} className="breadcrumbs__item">
        {item.name}
      </Link>
    );

    return (
      <span key={item.key} className="breadcrumbs__separator">
        {' > '}
        {content}
      </span>
    );
  };

  const getPathBreadcrumbs = () => {
    const paths = location.pathname.split('/').filter(Boolean);
    
    if (paths.length === 0) {
      return null;
    }

    const breadcrumbItems = paths.map((path, index) => {
      const routeTo = `/${paths.slice(0, index + 1).join('/')}`;
      const name = BREADCRUMB_MAP[path] || path;
      
      return {
        key: routeTo,
        name,
        routeTo,
        isLast: index === paths.length - 1,
      };
    });

    return breadcrumbItems;
  };

  const getCustomBreadcrumbs = () => {
    return customPath.map((item, index) => ({
      key: item.id,
      name: item.name,
      isLast: index === customPath.length - 1,
    }));
  };

  if (customPath?.length > 0) {
    const breadcrumbItems = getCustomBreadcrumbs();
    
    return (
      <nav className="breadcrumbs">
        <div className="breadcrumbs__container">
          <Link to="/" className="breadcrumbs__item breadcrumbs__home">
            Главная
          </Link>
          {breadcrumbItems.map(item => 
            renderBreadcrumbItem(item, item.isLast, true)
          )}
        </div>
      </nav>
    );
  }

  const breadcrumbItems = getPathBreadcrumbs();
  
  if (!breadcrumbItems) {
    return null;
  }

  return (
    <nav className="breadcrumbs">
      <div className="breadcrumbs__container">
        <Link to="/" className="breadcrumbs__item breadcrumbs__home">
          Главная
        </Link>
        {breadcrumbItems.map(item => 
          renderBreadcrumbItem(item, item.isLast, false)
        )}
      </div>
    </nav>
  );
};

export default Breadcrumbs;
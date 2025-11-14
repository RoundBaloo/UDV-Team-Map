
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Breadcrumbs.css';

const Breadcrumbs = ({ customPath }) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Обработчик клика по хлебной крошке
  const handleBreadcrumbClick = (item, event) => {
    event.preventDefault();
    
    // Сохраняем информацию о выбранном узле в sessionStorage
    sessionStorage.setItem('selectedOrgUnit', JSON.stringify({
      id: item.id,
      name: item.name,
      unit_type: item.unit_type,
    }));
    
    // Переходим на главную страницу
    navigate('/');
  };

  // Если передан кастомный путь, используем его
  if (customPath && customPath.length > 0) {
    return (
      <nav className="breadcrumbs">
        <div className="breadcrumbs__container">
          <Link to="/" className="breadcrumbs__item breadcrumbs__home">
            Главная
          </Link>
          
          {customPath.map((item, index) => {
            const isLast = index === customPath.length - 1;
            
            return (
              <span key={item.id} className="breadcrumbs__separator">
                {' > '}
                {isLast ? (
                  <span className="breadcrumbs__current">
                    {item.name}
                  </span>
                ) : (
                  <a 
                    href="/" 
                    className="breadcrumbs__item"
                    onClick={(e) => handleBreadcrumbClick(item, e)}
                  >
                    {item.name}
                  </a>
                )}
              </span>
            );
          })}
        </div>
      </nav>
    );
  }

  // Старая логика для других страниц
  const paths = location.pathname.split('/').filter(path => path);

  const getBreadcrumbName = (path, index) => {
    const breadcrumbMap = {
      '': 'Главная',
      'admin': 'Админка',
      'users': 'Пользователи',
      'photos': 'Фотографии',
      'profile': 'Профиль',
      'team': 'Команда',
    };

    return breadcrumbMap[path] || path;
  };

  if (paths.length === 0) {
    return null;
  }

  return (
    <nav className="breadcrumbs">
      <div className="breadcrumbs__container">
        <Link to="/" className="breadcrumbs__item breadcrumbs__home">
          Главная
        </Link>
        
        {paths.map((path, index) => {
          const routeTo = `/${paths.slice(0, index + 1).join('/')}`;
          const isLast = index === paths.length - 1;
          
          return (
            <span key={routeTo} className="breadcrumbs__separator">
              {' > '}
              {isLast ? (
                <span className="breadcrumbs__current">
                  {getBreadcrumbName(path, index)}
                </span>
              ) : (
                <Link to={routeTo} className="breadcrumbs__item">
                  {getBreadcrumbName(path, index)}
                </Link>
              )}
            </span>
          );
        })}
      </div>
    </nav>
  );
};

export default Breadcrumbs;
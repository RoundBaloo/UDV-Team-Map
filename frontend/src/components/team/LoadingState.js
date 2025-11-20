import React from 'react';
import Header from '../common/Header';
import Breadcrumbs from '../common/Breadcrumbs';

const LoadingState = ({ breadcrumbPath }) => {
  return (
    <div className="team-page">
      <Header />
      <Breadcrumbs customPath={breadcrumbPath} />
      <main className="team-main">
        <div className="container">
          <div className="loading-placeholder">Загрузка информации о команде...</div>
        </div>
      </main>
    </div>
  );
};

export default LoadingState;
import React from 'react';
import Header from '../common/Header';
import Breadcrumbs from '../common/Breadcrumbs';

const ErrorState = ({ breadcrumbPath }) => {
  return (
    <div className="team-page">
      <Header />
      <Breadcrumbs customPath={breadcrumbPath} />
      <main className="team-main">
        <div className="container">
          <div className="error-placeholder">Команда не найдена</div>
        </div>
      </main>
    </div>
  );
};

export default ErrorState;
import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ size = 'medium', text = 'Загрузка...' }) => {
  return (
    <div className={`loading-spinner loading-spinner--${size}`}>
      <div className="loading-spinner__animation" /> 
      {text && <div className="loading-spinner__text">{text}</div>}
    </div>
  );
};

export default LoadingSpinner;
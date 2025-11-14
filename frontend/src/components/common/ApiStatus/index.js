import React, { useState, useEffect } from 'react';
import { healthApi } from '../../../services/api/health';
import './ApiStatus.css';

const ApiStatus = () => {
  const [status, setStatus] = useState('checking');
  const [details, setDetails] = useState('');

  useEffect(() => {
    const checkApi = async () => {
      try {
        setStatus('checking');
        setDetails('Проверка подключения к API...');
        
        const healthResult = await healthApi.checkHealth();
        
        if (healthResult.success) {
          setStatus('connected');
          setDetails('API доступен');
        } else {
          setStatus('error');
          setDetails(`Ошибка: ${healthResult.error}`);
        }
      } catch (err) {
        setStatus('error');
        setDetails(`Не удалось проверить API: ${err.message}`);
      }
    };

    checkApi();
    
    // Периодическая проверка каждые 30 секунд
    const interval = setInterval(checkApi, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={`api-status api-status--${status}`}>
      <div className="api-status__indicator" />
      <div className="api-status__content">
        <div className="api-status__text">
          {status === 'checking' && 'Проверка подключения...'}
          {status === 'connected' && 'API подключен'}
          {status === 'error' && 'Ошибка подключения'}
        </div>
        {details && (
          <div className="api-status__details">{details}</div>
        )}
      </div>
    </div>
  );
};

export default ApiStatus;
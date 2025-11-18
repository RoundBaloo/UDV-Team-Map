import React, { useState, useEffect } from 'react';
import { healthApi } from '../../../services/api/health';
import './ApiStatus.css';

const CHECK_INTERVAL = 30000; // 30 секунд

const STATUS_CONFIG = {
  checking: { text: 'Проверка подключения...', details: 'Проверка подключения к API...' },
  connected: { text: 'API подключен', details: 'API доступен' },
  error: { text: 'Ошибка подключения', details: '' },
};

const ApiStatus = () => {
  const [status, setStatus] = useState('checking');
  const [details, setDetails] = useState('');

  useEffect(() => {
    let isMounted = true;

    const checkApi = async () => {
      try {
        if (isMounted) {
          setStatus('checking');
          setDetails(STATUS_CONFIG.checking.details);
        }
        
        const healthResult = await healthApi.checkHealth();
        
        if (isMounted) {
          if (healthResult.success) {
            setStatus('connected');
            setDetails(STATUS_CONFIG.connected.details);
          } else {
            setStatus('error');
            setDetails(`Ошибка: ${healthResult.error}`);
          }
        }
      } catch (err) {
        if (isMounted) {
          setStatus('error');
          setDetails(`Не удалось проверить API: ${err.message}`);
        }
      }
    };

    checkApi();
    
    const interval = setInterval(checkApi, CHECK_INTERVAL);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const statusInfo = STATUS_CONFIG[status] || STATUS_CONFIG.error;

  return (
    <div className={`api-status api-status--${status}`}>
      <div className="api-status__indicator" />
      <div className="api-status__content">
        <div className="api-status__text">
          {statusInfo.text}
        </div>
        {details && (
          <div className="api-status__details">{details}</div>
        )}
      </div>
    </div>
  );
};

export default ApiStatus;
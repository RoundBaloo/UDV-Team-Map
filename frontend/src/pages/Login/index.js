import React, { useState, useEffect } from 'react';
import { useAuth } from '../../services/auth/useAuth';
import { isValidEmail } from '../../utils/helpers';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiStatus, setApiStatus] = useState({ status: 'loading', text: 'Проверка соединения...' });
  
  const { login, error: authError } = useAuth();

  // Простая проверка доступности API
  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const response = await fetch('/health', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          setApiStatus({ status: 'success', text: 'Сервер доступен' });
        } else {
          setApiStatus({ status: 'error', text: 'Сервер недоступен' });
        }
      } catch (error) {
        setApiStatus({ status: 'error', text: 'Сервер недоступен' });
      }
    };

    checkApiHealth();
  }, []);

  const validateForm = () => {
    const newErrors = {};

    if (!email.trim()) {
      newErrors.email = 'Email обязателен';
    } else if (!isValidEmail(email)) {
      newErrors.email = 'Введите корректный email';
    }

    if (!password) {
      newErrors.password = 'Пароль обязателен';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    const result = await login(email, password);
    
    if (!result.success) {
      setErrors({ submit: result.error });
    }
    
    setIsSubmitting(false);
  };

  const handleInputChange = (setter, fieldName) => (e) => {
    setter(e.target.value);
    // Очищаем ошибки при вводе
    if (errors[fieldName]) {
      setErrors(prev => ({ ...prev, [fieldName]: '' }));
    }
    if (errors.submit) {
      setErrors(prev => ({ ...prev, submit: '' }));
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <h1 className="login-title">UDV Team Map</h1>
          <p className="login-subtitle">Войдите в свою учетную запись</p>
          
          <div className="api-status-minimal">
            <div className={`api-status-dot api-status-dot--${apiStatus.status}`} />
            <span>{apiStatus.text}</span>
          </div>
          
          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Корпоративная почта
              </label>
              <input
                id="email"
                name="email"
                type="email"
                className={`form-input ${errors.email ? 'form-input--error' : ''}`}
                placeholder="ivanov@udv.com"
                value={email}
                onChange={handleInputChange(setEmail, 'email')}
                disabled={isSubmitting}
              />
              {errors.email && <div className="form-error">{errors.email}</div>}
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Пароль
              </label>
              <input
                id="password"
                name="password"
                type="password"
                className={`form-input ${errors.password ? 'form-input--error' : ''}`}
                placeholder="Введите пароль"
                value={password}
                onChange={handleInputChange(setPassword, 'password')}
                disabled={isSubmitting}
              />
              {errors.password && <div className="form-error">{errors.password}</div>}
            </div>

            {(errors.submit || authError) && (
              <div className="form-error form-error--submit">
                {errors.submit || authError}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary login-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Вход...' : 'Войти'}
            </button>
          </form>

          <div className="login-help">
            <p>Используйте корпоративные учетные данные для входа</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
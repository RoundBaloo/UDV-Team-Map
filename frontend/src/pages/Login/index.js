import React, { useState, useEffect } from 'react';
import { useAuth } from '../../services/auth/useAuth';
import { isValidEmail } from '../../utils/helpers';
import './Login.css';

const API_STATUS = {
  LOADING: { status: 'loading', text: 'Проверка соединения...' },
  SUCCESS: { status: 'success', text: 'Сервер доступен' },
  ERROR: { status: 'error', text: 'Сервер недоступен' },
};

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiStatus, setApiStatus] = useState(API_STATUS.LOADING);
  
  const { login, error: authError } = useAuth();

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await fetch('/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        setApiStatus(API_STATUS.SUCCESS);
      } else {
        setApiStatus(API_STATUS.ERROR);
      }
    } catch (error) {
      setApiStatus(API_STATUS.ERROR);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email обязателен';
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = 'Введите корректный email';
    }

    if (!formData.password) {
      newErrors.password = 'Пароль обязателен';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async e => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    const result = await login(formData.email, formData.password);
    
    if (!result.success) {
      setErrors(prev => ({ ...prev, submit: result.error }));
    }
    
    setIsSubmitting(false);
  };

  const handleInputChange = field => e => {
    const value = e.target.value;
    
    setFormData(prev => ({ ...prev, [field]: value }));
    
    if (errors[field] || errors.submit) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        delete newErrors.submit;
        return newErrors;
      });
    }
  };

  const submitError = errors.submit || authError;

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <h1 className="login-title">UDV Team Map</h1>
          <p className="login-subtitle">Войдите в свою учетную запись</p>
          
          <ApiStatus status={apiStatus} />
          
          <LoginForm
            formData={formData}
            errors={errors}
            submitError={submitError}
            isSubmitting={isSubmitting}
            onInputChange={handleInputChange}
            onSubmit={handleSubmit}
          />

          <LoginHelp />
        </div>
      </div>
    </div>
  );
};

const ApiStatus = ({ status }) => (
  <div className="api-status-minimal">
    <div className={`api-status-dot api-status-dot--${status.status}`} />
    <span>{status.text}</span>
  </div>
);

const LoginForm = ({ 
  formData, 
  errors, 
  submitError, 
  isSubmitting, 
  onInputChange, 
  onSubmit,
}) => {
  return (
    <form onSubmit={onSubmit} className="login-form">
      <FormField
        id="email"
        label="Корпоративная почта"
        type="email"
        value={formData.email}
        error={errors.email}
        placeholder="ivanov@udv.com"
        onChange={onInputChange('email')}
        disabled={isSubmitting}
      />

      <FormField
        id="password"
        label="Пароль"
        type="password"
        value={formData.password}
        error={errors.password}
        placeholder="Введите пароль"
        onChange={onInputChange('password')}
        disabled={isSubmitting}
      />

      {submitError && (
        <div className="form-error form-error--submit">
          {submitError}
        </div>
      )}

      <SubmitButton isSubmitting={isSubmitting} />
    </form>
  );
};

const FormField = ({ 
  id, 
  label, 
  type, 
  value, 
  error, 
  placeholder, 
  onChange, 
  disabled,
}) => {
  return (
    <div className="form-group">
      <label htmlFor={id} className="form-label">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        className={`form-input ${error ? 'form-input--error' : ''}`}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
      {error && <div className="form-error">{error}</div>}
    </div>
  );
};

const SubmitButton = ({ isSubmitting }) => (
  <button
    type="submit"
    className="btn btn-primary login-button"
    disabled={isSubmitting}
  >
    {isSubmitting ? 'Вход...' : 'Войти'}
  </button>
);

const LoginHelp = () => (
  <div className="login-help">
    <p>Используйте корпоративные учетные данные для входа</p>
  </div>
);

export default Login;
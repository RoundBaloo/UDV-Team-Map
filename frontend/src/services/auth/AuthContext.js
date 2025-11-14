import React, { createContext, useState, useEffect, useContext } from 'react';
import { authApi } from '../api/auth';
import { employeesApi } from '../api/employees';
import { tokenStorage } from '../storage/tokenStorage';

// Создаем контекст
const AuthContext = createContext();

// Провайдер аутентификации
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Проверяем авторизацию при загрузке
  useEffect(() => {
    checkAuth();
  }, []);

  // Проверить авторизацию
  const checkAuth = async () => {
    const token = tokenStorage.getToken();
    
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      // Получаем базовые данные пользователя через auth/me
      const authData = await authApi.getMe();
      console.log('Auth data:', authData);
      
      // ИСПРАВЛЕНО: используем employee_id вместо id
      const userData = await employeesApi.getEmployee(authData.employee_id);
      console.log('User data:', userData);
      
      setUser(userData);
      setError(null);
    } catch (err) {
      console.error('Auth check failed:', err);
      // Если ошибка 401, удаляем токен
      if (err.status === 401) {
        tokenStorage.removeToken();
      }
      setUser(null);
      setError('Сессия истекла. Пожалуйста, войдите снова.');
    } finally {
      setLoading(false);
    }
  };

  // Вход
  const login = async (email, password) => {
    try {
      setLoading(true);
      setError(null);
      
      // 1. Логинимся и получаем токен
      const response = await authApi.login(email, password);
      tokenStorage.setToken(response.access_token);
      
      // 2. Получаем базовые данные пользователя
      const authData = await authApi.getMe();
      console.log('Auth data after login:', authData);
      
      // 3. ИСПРАВЛЕНО: используем employee_id вместо id
      const userData = await employeesApi.getEmployee(authData.employee_id);
      console.log('Full user data:', userData);
      
      setUser(userData);
      
      return { success: true };
    } catch (err) {
      const errorMessage = err.message || 'Ошибка входа';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Выход
  const logout = () => {
    tokenStorage.removeToken();
    setUser(null);
    setError(null);
  };

  // Обновить данные пользователя
  const updateUser = (userData) => {
    setUser(prev => ({ ...prev, ...userData }));
  };

  // Обновить данные пользователя на сервере
  const updateUserProfile = async (userData) => {
    // ИСПРАВЛЕНО: используем employee_id вместо id
    if (!user?.employee_id) {
      return { success: false, error: 'ID пользователя не найден' };
    }

    try {
      const updatedUser = await employeesApi.updateEmployee(user.employee_id, userData);
      setUser(updatedUser);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  // Проверить права администратора
  const isAdmin = user?.is_admin === true;

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    updateUser,
    updateUserProfile,
    isAdmin,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Хук для использования контекста
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
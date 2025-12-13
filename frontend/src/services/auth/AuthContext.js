import React, { createContext, useState, useEffect, useContext } from 'react';
import { authApi } from '../api/auth';
import { employeesApi } from '../api/employees';
import { tokenStorage } from '../storage/tokenStorage';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = tokenStorage.getToken();
    
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const authData = await authApi.getMe();
      console.log('Auth data:', authData);
      
      const userData = await employeesApi.getEmployee(authData.employee_id);
      console.log('User data:', userData);
      
      setUser(userData);
      setError(null);
    } catch (err) {
      console.error('Auth check failed:', err);
      if (err.status === 401) {
        tokenStorage.removeToken();
      }
      setUser(null);
      setError('Сессия истекла. Пожалуйста, войдите снова.');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authApi.login(email, password);
      tokenStorage.setToken(response.access_token);
      
      const authData = await authApi.getMe();
      console.log('Auth data after login:', authData);
      
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

  const logout = () => {
    tokenStorage.removeToken();
    setUser(null);
    setError(null);
  };

  const updateUser = (userData) => {
    setUser(prev => ({ ...prev, ...userData }));
  };

  const updateUserProfile = async (userData) => {
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

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './services/auth/AuthContext';
import { useAuth } from './services/auth/useAuth';
import LoadingSpinner from './components/common/LoadingSpinner';
import Login from './pages/Login';
import OrgStructure from './pages/OrgStructure';
import TeamPage from './pages/TeamPage';
import Profile from './pages/Profile';
import AdminUsersTable from './pages/AdminUsersTable';
import PhotoModeration from './pages/PhotoModeration';
import './App.css';

// Компонент защищенного маршрута
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Публичный маршрут (редирект если уже авторизован)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function AppContent() {
  return (
    <div className="app">
      <Routes>
        {/* Публичные маршруты */}
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } 
        />
        
        {/* Защищенные маршруты */}
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <OrgStructure />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/profile/:id?" 
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/team/:id" 
          element={
            <ProtectedRoute>
              <TeamPage />
            </ProtectedRoute>
          } 
        />
        
        {/* Админские маршруты */}
        <Route 
          path="/admin/users" 
          element={
            <ProtectedRoute requireAdmin={true}>
              <AdminUsersTable />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/photos" 
          element={
            <ProtectedRoute requireAdmin={true}>
              <PhotoModeration />
            </ProtectedRoute>
          } 
        />
        
        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
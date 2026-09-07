import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingBar from './LoadingBar';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  // The session check is a single request. A full-page spinner and a "Loading
  // League Analytics…" caption overstate it; a rule at the top of the viewport
  // is enough, and it does not flash a layout that is about to be replaced.
  if (isLoading) {
    return <LoadingBar label="Checking session" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;

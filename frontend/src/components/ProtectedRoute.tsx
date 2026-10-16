/**
 * Protected Route Authorization Guard
 * =====================================
 * Restricts access to authenticated users only.
 * Redirects unauthenticated visitors to the master terminal login page.
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#0c0d10',
          color: '#ffffff',
          fontFamily: 'Inter, sans-serif',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              border: '3px solid rgba(0, 208, 156, 0.2)',
              borderTopColor: '#00d09c',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
              margin: '0 auto 12px auto',
            }}
          />
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Verifying Master Trader Session...
          </span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Preserve attempted destination
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;

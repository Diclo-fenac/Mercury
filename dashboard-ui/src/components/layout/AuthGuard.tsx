import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { checkAuth } from '../../lib/auth-api';

export const AuthGuard = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, setAuth } = useAuthStore();
  const [isVerifying, setIsVerifying] = useState(!isAuthenticated);
  const location = useLocation();

  useEffect(() => {
    if (!isAuthenticated) {
      checkAuth()
        .then(() => {
          setAuth();
        })
        .catch(() => {
          // not authenticated
        })
        .finally(() => {
          setIsVerifying(false);
        });
    } else {
      setIsVerifying(false);
    }
  }, [isAuthenticated, setAuth]);

  if (isVerifying) {
    return <div className="min-h-screen flex items-center justify-center">Verifying session...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

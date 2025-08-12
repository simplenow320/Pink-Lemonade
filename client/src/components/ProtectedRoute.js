import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children, requireOrganization = false }) => {
  const { authenticated, user, organization, loading } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!authenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If authenticated but requires organization setup
  if (requireOrganization && (!organization || !organization.profile_completeness || organization.profile_completeness < 50)) {
    return <Navigate to="/onboarding" replace />;
  }

  // Check for paywall (simple example - could be more sophisticated)
  if (requireOrganization && user && !user.subscription_active && organization && organization.profile_completeness >= 50) {
    return <Navigate to="/paywall" replace />;
  }

  return children;
};

export default ProtectedRoute;
import React, { useState, useEffect, lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { initializeOrganization, ApiError } from './utils/api';
import { useNotification } from './context/NotificationContext';
import { useAuth } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

// Modern layout
import ModernLayout from './components/layout/ModernLayout';

// Import pages using lazy loading for better performance
const Landing = lazy(() => import('./pages/Landing'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const OrganizationOnboarding = lazy(() => import('./pages/OrganizationOnboarding'));
const Paywall = lazy(() => import('./pages/Paywall'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Grants = lazy(() => import('./pages/Grants'));
const GrantDetail = lazy(() => import('./pages/GrantDetail'));
const Organization = lazy(() => import('./pages/Organization'));
const Profile = lazy(() => import('./pages/Profile'));
const Onboarding = lazy(() => import('./pages/Onboarding'));
const Narrative = lazy(() => import('./pages/Narrative'));
const Scraper = lazy(() => import('./pages/Scraper'));
const Analytics = lazy(() => import('./pages/Analytics'));
const WritingAssistant = lazy(() => import('./pages/WritingAssistant'));
const SmartTools = lazy(() => import('./pages/SmartTools'));
const Survey = lazy(() => import('./pages/Survey'));
const CaseSupport = lazy(() => import('./pages/CaseSupport'));
const GrantPitch = lazy(() => import('./pages/GrantPitch'));
const ImpactReport = lazy(() => import('./pages/ImpactReport'));
const Templates = lazy(() => import('./pages/Templates'));
const Governance = lazy(() => import('./pages/Governance'));

// Loading component for suspense fallback
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[70vh]">
    <div className="flex flex-col items-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      <p className="mt-4 text-gray-600">Loading...</p>
    </div>
  </div>
);

function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { addError } = useNotification();
  const { authenticated, loading: authLoading } = useAuth();

  // Initialize app data on first load, but only if authenticated
  useEffect(() => {
    const initialize = async () => {
      try {
        console.log('Pink Lemonade application initialized');
        // Only initialize organization data if user is authenticated
        if (authenticated) {
          const result = await initializeOrganization();
        }
      } catch (err) {
        console.error('Error initializing application:', err);

        const errorMessage =
          err instanceof ApiError
            ? err.message
            : 'Failed to initialize application. Please reload the page.';

        setError(errorMessage);
        addError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    // Wait for auth check to complete before initializing
    if (!authLoading) {
      initialize();
    }
  }, [addError, authenticated, authLoading]);

  // App loading screen (show if auth or app is loading)
  if (loading || authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="flex flex-col items-center">
            <div className="inline-block animate-spin h-10 w-10 border-4 border-pink-500 border-t-transparent rounded-full mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-700">Loading Pink Lemonade...</h2>
            <p className="mt-2 text-sm text-gray-500">
              Connecting to your grant discovery platform
            </p>
          </div>
        </div>
      </div>
    );
  }

  // App error screen
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center max-w-md p-8 bg-white rounded-xl shadow-lg">
          <div className="bg-red-100 p-3 rounded-full inline-flex mb-4">
            <svg
              className="w-8 h-8 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full px-4 py-2 bg-pink-500 text-white rounded-lg font-medium hover:bg-pink-600 transition-colors shadow-md hover:shadow-lg"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Modern app layout with authentication routes
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public routes - Landing page */}
        <Route
          path="/"
          element={
            <ErrorBoundary>
              <Landing />
            </ErrorBoundary>
          }
        />

        {/* Authentication routes - no layout */}
        <Route
          path="/login"
          element={
            <ErrorBoundary>
              <Login />
            </ErrorBoundary>
          }
        />
        <Route
          path="/register"
          element={
            <ErrorBoundary>
              <Register />
            </ErrorBoundary>
          }
        />

        {/* Organization onboarding - protected, no layout */}
        <Route
          path="/onboarding"
          element={
            <ErrorBoundary>
              <ProtectedRoute>
                <OrganizationOnboarding />
              </ProtectedRoute>
            </ErrorBoundary>
          }
        />

        {/* Paywall - protected, no layout */}
        <Route
          path="/paywall"
          element={
            <ErrorBoundary>
              <ProtectedRoute>
                <Paywall />
              </ProtectedRoute>
            </ErrorBoundary>
          }
        />

        {/* Survey route - public access with project ID */}
        <Route
          path="/survey/:projectId"
          element={
            <ErrorBoundary>
              <Survey />
            </ErrorBoundary>
          }
        />
        
        {/* Protected app routes with ModernLayout */}
        <Route
          path="/*"
          element={
            <ProtectedRoute requireOrganization={true}>
              <ModernLayout>
                <Routes>
                  <Route
                    path="/dashboard"
                    element={
                      <ErrorBoundary>
                        <Dashboard />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/grants"
                    element={
                      <ErrorBoundary>
                        <Grants />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/grants/:id"
                    element={
                      <ErrorBoundary>
                        <GrantDetail />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/organization"
                    element={
                      <ErrorBoundary>
                        <Organization />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/profile"
                    element={
                      <ErrorBoundary>
                        <Profile />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/narratives/:grantId"
                    element={
                      <ErrorBoundary>
                        <Narrative />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/scraper"
                    element={
                      <ErrorBoundary>
                        <Scraper />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/analytics"
                    element={
                      <ErrorBoundary>
                        <Analytics />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/writing-assistant"
                    element={
                      <ErrorBoundary>
                        <WritingAssistant />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/writing-assistant/:grantId"
                    element={
                      <ErrorBoundary>
                        <WritingAssistant />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/smart-tools"
                    element={
                      <ErrorBoundary>
                        <SmartTools />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/smart-tools/:toolId"
                    element={
                      <ErrorBoundary>
                        <SmartTools />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/templates"
                    element={
                      <ErrorBoundary>
                        <Templates />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/governance"
                    element={
                      <ErrorBoundary>
                        <Governance />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/case-support"
                    element={
                      <ErrorBoundary>
                        <CaseSupport />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/grant-pitch"
                    element={
                      <ErrorBoundary>
                        <GrantPitch />
                      </ErrorBoundary>
                    }
                  />
                  <Route
                    path="/impact-report"
                    element={
                      <ErrorBoundary>
                        <ImpactReport />
                      </ErrorBoundary>
                    }
                  />
                  {/* Redirect /reports to /smart-tools */}
                  <Route path="/reports" element={<Navigate to="/smart-tools" replace />} />
                  
                  {/* Fallback route for any other paths */}
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </ModernLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  );
}

export default App;

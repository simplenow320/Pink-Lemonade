import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import GrantsPage from './pages/GrantsPage';
import GrantDetailPage from './pages/GrantDetailPage';
import ProfilePage from './pages/ProfilePage';
import NarrativePage from './pages/NarrativePage';
import ScraperPage from './pages/ScraperPage';
import AnalyticsPage from './pages/AnalyticsPage';
import WritingAssistantPage from './pages/WritingAssistantPage';
import { initializeOrganization, ApiError } from './utils/api';
import { useNotification } from './context/NotificationContext';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { addError } = useNotification();
  
  // Initialize app data on first load
  useEffect(() => {
    const initialize = async () => {
      try {
        // First check if we have an organization profile
        const result = await initializeOrganization();
        console.log('Organization initialization result:', result);
      } catch (err) {
        console.error('Error initializing application:', err);
        
        // Use the error message from ApiError if available
        const errorMessage = err instanceof ApiError
          ? err.message
          : 'Failed to initialize application. Please reload the page.';
          
        setError(errorMessage);
        addError(errorMessage);
      } finally {
        setLoading(false);
      }
    };
    
    initialize();
  }, [addError]);
  
  // Show loading screen while initializing
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">Loading GrantFlow...</h2>
        </div>
      </div>
    );
  }
  
  // Show error screen if initialization failed
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center max-w-md p-6 bg-white rounded-lg shadow-md">
          <svg className="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="py-6 px-4 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={
              <ErrorBoundary>
                <DashboardPage />
              </ErrorBoundary>
            } />
            <Route path="/grants" element={
              <ErrorBoundary>
                <GrantsPage />
              </ErrorBoundary>
            } />
            <Route path="/grants/:id" element={
              <ErrorBoundary>
                <GrantDetailPage />
              </ErrorBoundary>
            } />
            <Route path="/organization" element={
              <ErrorBoundary>
                <ProfilePage />
              </ErrorBoundary>
            } />
            <Route path="/narratives/:grantId" element={
              <ErrorBoundary>
                <NarrativePage />
              </ErrorBoundary>
            } />
            <Route path="/scraper" element={
              <ErrorBoundary>
                <ScraperPage />
              </ErrorBoundary>
            } />
            <Route path="/analytics" element={
              <ErrorBoundary>
                <AnalyticsPage />
              </ErrorBoundary>
            } />
            <Route path="/writing-assistant" element={
              <ErrorBoundary>
                <WritingAssistantPage />
              </ErrorBoundary>
            } />
            <Route path="/writing-assistant/:grantId" element={
              <ErrorBoundary>
                <WritingAssistantPage />
              </ErrorBoundary>
            } />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default App;

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useGrants } from '../hooks/useGrants';
import { formatCurrency, formatDate } from '../utils/formatters';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import WelcomeAnimation from '../components/ui/WelcomeAnimation';
import ProfileRewards from '../components/ui/ProfileRewards';
import ErrorVisualization from '../components/ui/ErrorVisualization';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const Dashboard = () => {
  const { grants, loading, error, dashboardData } = useGrants({ includeDashboard: true });
  const [upcomingGrants, setUpcomingGrants] = useState([]);
  const [topMatchingGrants, setTopMatchingGrants] = useState([]);

  useEffect(() => {
    if (grants && grants.length > 0) {
      // Filter grants for upcoming deadlines (next 30 days)
      const today = new Date();
      const thirtyDaysFromNow = new Date();
      thirtyDaysFromNow.setDate(today.getDate() + 30);
      
      const upcoming = grants
        .filter(grant => {
          if (!grant.due_date) return false;
          const dueDate = new Date(grant.due_date);
          return dueDate >= today && dueDate <= thirtyDaysFromNow;
        })
        .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
        .slice(0, 5);
      
      setUpcomingGrants(upcoming);
      
      // Filter for top matching grants
      const matching = [...grants]
        .filter(grant => grant.match_score >= 70)
        .sort((a, b) => b.match_score - a.match_score)
        .slice(0, 5);
      
      setTopMatchingGrants(matching);
    }
  }, [grants]);
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-pink-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <ErrorVisualization
        type="server"
        error={error}
        solution="Try refreshing the page. If this keeps happening, check your internet connection."
        onRetry={() => window.location.reload()}
      />
    );
  }

  // Format status name with color
  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'Not Started':
        return 'bg-gray-100 text-gray-800';
      case 'In Progress':
        return 'bg-blue-100 text-blue-800';
      case 'Submitted':
        return 'bg-yellow-100 text-yellow-800';
      case 'Won':
        return 'bg-green-100 text-green-800';
      case 'Declined':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Format match score with color
  const getMatchScoreClass = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-green-500';
    if (score >= 50) return 'text-yellow-500';
    if (score >= 30) return 'text-orange-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-8">
      {/* Welcome Animation */}
      <WelcomeAnimation 
        userName="Admin"
        orgName="Pink Lemonade User"
        isFirstVisit={!grants || grants.length === 0}
      />

      {/* Page Header with CTA */}
      <div className="flex flex-col lg:flex-row justify-between lg:items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Grant Management Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Overview of your grant activities and opportunities
          </p>
        </div>
        <div className="mt-4 lg:mt-0 flex flex-col sm:flex-row gap-3">
          <Link
            to="/scraper"
            className="btn-primary inline-flex items-center justify-center"
          >
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Find New Grants
          </Link>
          <Link
            to="/grants"
            className="btn-secondary inline-flex items-center justify-center"
          >
            View All Grants
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      {dashboardData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-white overflow-hidden shadow-sm rounded-xl p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-orange-100 rounded-lg p-3">
                <svg className="h-6 w-6 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Grant Opportunities
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {dashboardData.total_grants || 0}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow-sm rounded-xl p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-green-100 rounded-lg p-3">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Funding Available
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {dashboardData.total_funding ? formatCurrency(dashboardData.total_funding) : '$0'}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow-sm rounded-xl p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-100 rounded-lg p-3">
                <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    High Matching Grants
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {dashboardData.high_match_count || 0}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow-sm rounded-xl p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-purple-100 rounded-lg p-3">
                <svg className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Submitted Grants
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {dashboardData.status_counts?.Submitted || 0}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts and Profile Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column - Charts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Grant Status Chart */}
          <div className="bg-white shadow-sm rounded-xl overflow-hidden p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Grant Status Overview</h2>
            <div className="h-64 flex items-center justify-center">
              {dashboardData?.status_counts && Object.keys(dashboardData.status_counts).length > 0 ? (
                <div className="text-center text-gray-500">
                  Chart visualization coming soon
                </div>
              ) : (
                <div className="text-center text-gray-500">
                  No data available
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Right column - Profile Rewards */}
        <div className="lg:col-span-1 space-y-6">
          <ProfileRewards 
            completionPercentage={85}
            completedSections={['basic_info', 'programs', 'capacity']}
            totalSections={5}
          />
        </div>
      </div>

      {/* Grant Lists Section */}
      <div className="space-y-8">
        {/* Upcoming Deadlines */}
        <div className="bg-white shadow-sm rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Upcoming Deadlines</h2>
          </div>
          {upcomingGrants.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {upcomingGrants.map((grant) => (
                <Link key={grant.id} to={`/grants/${grant.id}`} className="block px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer">
                  <div className="flex items-center">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-medium text-gray-900 hover:text-orange-600">
                        {grant.title}
                      </h3>
                      <div className="mt-1 flex items-center text-sm text-gray-500">
                        <span className="truncate">{grant.funder}</span>
                        <span className="mx-1">•</span>
                        <span className="font-medium text-pink-600">
                          Due: {formatDate(grant.due_date)}
                        </span>
                      </div>
                    </div>
                    <div className="ml-6 flex-shrink-0">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(grant.status)}`}>
                        {grant.status}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="px-6 py-10 text-center text-gray-500">
              <p className="text-sm">No upcoming deadlines</p>
            </div>
          )}
          <div className="px-6 py-3 bg-gray-50 text-right">
            <Link to="/grants" className="text-sm font-medium text-orange-600 hover:text-orange-500">
              View all grants →
            </Link>
          </div>
        </div>

        {/* High Matching Grants */}
        <div className="bg-white shadow-sm rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">High Matching Grants</h2>
          </div>
          {topMatchingGrants.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {topMatchingGrants.map((grant) => (
                <Link key={grant.id} to={`/grants/${grant.id}`} className="block px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer">
                  <div className="flex items-center">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-medium text-gray-900 hover:text-orange-600">
                        {grant.title}
                      </h3>
                      <div className="mt-1 flex items-center text-sm text-gray-500">
                        <span className="truncate">{grant.funder}</span>
                        {grant.amount && (
                          <>
                            <span className="mx-1">•</span>
                            <span>{formatCurrency(grant.amount)}</span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="ml-6 flex-shrink-0">
                      <span className={`font-medium ${getMatchScoreClass(grant.match_score)}`}>
                        {grant.match_score}% Match
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="px-6 py-10 text-center text-gray-500">
              <p className="text-sm">No high matching grants found</p>
            </div>
          )}
          <div className="px-6 py-3 bg-gray-50 text-right">
            <Link to="/grants" className="text-sm font-medium text-orange-600 hover:text-orange-500">
              View all grants →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
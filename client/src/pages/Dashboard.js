import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useGrants } from '../hooks/useGrants';
import { formatCurrency, formatDate } from '../utils/formatters';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const Dashboard = () => {
  const { grants, loading, error, dashboardData } = useGrants({ includeDashboard: true });
  const [upcomingGrants, setUpcomingGrants] = useState([]);
  const [topMatchingGrants, setTopMatchingGrants] = useState([]);
  const [expandedGrants, setExpandedGrants] = useState({});

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
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const statusChartData = {
    labels: dashboardData?.status_counts ? Object.keys(dashboardData.status_counts) : [],
    datasets: [{
      data: dashboardData?.status_counts ? Object.values(dashboardData.status_counts) : [],
      backgroundColor: [
        '#E5E7EB', // Not Started - gray-200
        '#93C5FD', // In Progress - blue-300
        '#FCD34D', // Submitted - yellow-300
        '#6EE7B7', // Won - green-300
        '#FCA5A5'  // Declined - red-300
      ],
      borderColor: '#FFFFFF',
      borderWidth: 2
    }]
  };
  
  const matchChartData = {
    labels: dashboardData?.match_score_distribution ? Object.keys(dashboardData.match_score_distribution) : [],
    datasets: [{
      label: 'Number of Grants',
      data: dashboardData?.match_score_distribution ? Object.values(dashboardData.match_score_distribution) : [],
      backgroundColor: '#3B82F6', // primary color
      borderColor: '#2563EB',
      borderWidth: 1
    }]
  };

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
                    Total Grants
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
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Potential Funding
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {formatCurrency(dashboardData.potential_funding || 0)}
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
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Won Funding
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {formatCurrency(dashboardData.won_funding || 0)}
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
      
      {/* Latest Grant Opportunities - Mobile First View */}
      <div className="lg:hidden bg-white shadow-sm rounded-xl overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Latest Grant Opportunities</h2>
        </div>
        {grants.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {grants.slice(0, 5).map((grant) => (
              <div 
                key={grant.id} 
                onClick={() => setExpandedGrants(prev => ({ ...prev, [grant.id]: !prev[grant.id] }))}
                className="block px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0 pr-4">
                    <h3 className="text-base font-medium text-gray-900 mb-1 flex items-center">
                      {grant.title}
                      <svg 
                        className={`ml-2 h-4 w-4 transform transition-transform ${expandedGrants[grant.id] ? 'rotate-90' : ''}`} 
                        fill="currentColor" 
                        viewBox="0 0 20 20"
                      >
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                    </h3>
                    <p className={`text-sm text-gray-600 mb-2 ${!expandedGrants[grant.id] ? 'line-clamp-2' : ''}`}>
                      {grant.description || 'No description available'}
                    </p>
                    {expandedGrants[grant.id] && (
                      <div className="mt-3 space-y-2 border-t pt-3">
                        <div className="text-sm">
                          <span className="font-medium text-gray-700">Eligibility:</span>
                          <span className="ml-2 text-gray-600">{grant.eligibility || 'Not specified'}</span>
                        </div>
                        {grant.website && (
                          <div className="text-sm">
                            <span className="font-medium text-gray-700">Website:</span>
                            <a href={grant.website} target="_blank" rel="noopener noreferrer" className="ml-2 text-pink-600 hover:text-pink-700">
                              Visit Grant Page →
                            </a>
                          </div>
                        )}
                        {grant.match_explanation && (
                          <div className="text-sm">
                            <span className="font-medium text-gray-700">Match Reason:</span>
                            <span className="ml-2 text-gray-600">{grant.match_explanation}</span>
                          </div>
                        )}
                        <div className="text-sm">
                          <span className="font-medium text-gray-700">Status:</span>
                          <span className="ml-2 text-gray-600">{grant.status || 'Not Started'}</span>
                        </div>
                        <div className="flex gap-2 mt-3">
                          <button className="px-3 py-1 bg-pink-600 text-white text-sm rounded-md hover:bg-pink-700">
                            Apply Now
                          </button>
                          <button className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300">
                            Save to Library
                          </button>
                        </div>
                      </div>
                    )}
                    <div className="flex items-center text-xs text-gray-500 space-x-3">
                      <span className="flex items-center">
                        <svg className="mr-1 h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z"/>
                        </svg>
                        {grant.funder || 'Unknown Funder'}
                      </span>
                      {grant.amount && (
                        <span>{formatCurrency(grant.amount)}</span>
                      )}
                      {grant.due_date && (
                        <span>Due: {formatDate(grant.due_date)}</span>
                      )}
                    </div>
                  </div>
                  {grant.match_score && (
                    <div className="flex-shrink-0">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-pink-100 text-pink-800">
                        {grant.match_score}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-10 text-center text-gray-500">
            <svg className="mx-auto h-10 w-10 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm">No grant opportunities found</p>
            <Link to="/scraper" className="mt-3 inline-block text-sm font-medium text-orange-600 hover:text-orange-500">
              Discover new grants →
            </Link>
          </div>
        )}
        <div className="px-6 py-3 bg-gray-50 text-right">
          <Link to="/grants" className="text-sm font-medium text-orange-600 hover:text-orange-500">
            View all grants →
          </Link>
        </div>
      </div>

      {/* Charts and Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left column - Charts */}
        <div className="lg:col-span-2 space-y-8">
          {/* Status Distribution */}
          <div className="bg-white shadow-sm rounded-xl p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Grant Status Distribution</h2>
            <div className="h-64">
              {dashboardData?.status_counts ? (
                <Doughnut
                  data={statusChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom',
                        labels: {
                          padding: 20,
                          boxWidth: 12,
                          font: {
                            size: 11
                          }
                        }
                      }
                    },
                    cutout: '70%'
                  }}
                />
              ) : (
                <div className="flex justify-center items-center h-full text-gray-500">
                  No data available
                </div>
              )}
            </div>
          </div>
          
          {/* Match Score Distribution */}
          <div className="bg-white shadow-sm rounded-xl p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Match Score Distribution</h2>
            <div className="h-64">
              {dashboardData?.match_score_distribution ? (
                <Bar
                  data={matchChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: false
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: {
                          precision: 0
                        }
                      }
                    }
                  }}
                />
              ) : (
                <div className="flex justify-center items-center h-full text-gray-500">
                  No data available
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Right column - Lists */}
        <div className="lg:col-span-3 space-y-8">
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
                          <span className="font-medium text-orange-600">
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
                <svg className="mx-auto h-10 w-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="mt-2 text-sm">No upcoming deadlines in the next 30 days</p>
              </div>
            )}
            <div className="px-6 py-3 bg-gray-50 text-right">
              <Link to="/grants" className="text-sm font-medium text-orange-600 hover:text-orange-500">
                View all grants →
              </Link>
            </div>
          </div>
          
          {/* Top Matching Grants */}
          <div className="bg-white shadow-sm rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Top Matching Grants</h2>
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
                <svg className="mx-auto h-10 w-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="mt-2 text-sm">No high matching grants found</p>
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
    </div>
  );
};

export default Dashboard;
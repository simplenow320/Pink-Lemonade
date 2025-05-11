import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { formatCurrency, formatDate, getDateUrgencyClass, formatMatchScore, getMatchScoreClass, getStatusClass } from '../utils/formatters';
import { runScraper, getScraperHistory } from '../utils/api';
import { useGrants } from '../hooks/useGrants';
import Chart from 'chart.js/auto';

const Dashboard = () => {
  const { grants, loading, error, refreshData, dashboardData } = useGrants({ includeDashboard: true });
  const [chartInstances, setChartInstances] = useState({});
  const [isScraperRunning, setIsScraperRunning] = useState(false);
  
  useEffect(() => {
    if (dashboardData) {
      createCharts();
    }
    
    return () => {
      // Cleanup charts on unmount
      Object.values(chartInstances).forEach(chart => chart.destroy());
    };
  }, [dashboardData]);
  
  const createCharts = () => {
    // Destroy existing charts
    Object.values(chartInstances).forEach(chart => chart.destroy());
    
    const newChartInstances = {};
    
    // Status chart
    if (dashboardData && dashboardData.status_counts) {
      const statusCtx = document.getElementById('statusChart');
      if (statusCtx) {
        newChartInstances.status = new Chart(statusCtx, {
          type: 'doughnut',
          data: {
            labels: Object.keys(dashboardData.status_counts),
            datasets: [{
              data: Object.values(dashboardData.status_counts),
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
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  padding: 20,
                  boxWidth: 12
                }
              }
            },
            cutout: '70%'
          }
        });
      }
    }
    
    // Match score chart
    if (dashboardData && dashboardData.match_score_distribution) {
      const matchCtx = document.getElementById('matchChart');
      if (matchCtx) {
        newChartInstances.match = new Chart(matchCtx, {
          type: 'bar',
          data: {
            labels: Object.keys(dashboardData.match_score_distribution),
            datasets: [{
              label: 'Number of Grants',
              data: Object.values(dashboardData.match_score_distribution),
              backgroundColor: '#3B82F6', // primary color
              borderColor: '#2563EB',
              borderWidth: 1
            }]
          },
          options: {
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
          }
        });
      }
    }
    
    setChartInstances(newChartInstances);
  };
  
  const [scraperStatus, setScraperStatus] = useState({
    isRunning: false,
    sites: 0,
    queries: 0,
    successful: 0,
    grants: 0,
    message: ''
  });
  
  const checkScraperStatus = async () => {
    try {
      const statusData = await getScraperHistory(1);
      if (statusData && statusData.length > 0) {
        const latestJob = statusData[0];
        
        const isRunning = latestJob.status === 'in_progress';
        setScraperStatus({
          isRunning,
          // Try to get these properties from multiple places for backward compatibility
          sites: latestJob.sites_searched || 
                 (latestJob.search_report && latestJob.search_report.sites_searched) || 0,
          queries: latestJob.queries_attempted || 
                   (latestJob.search_report && latestJob.search_report.queries_attempted) || 0,
          successful: latestJob.successful_queries || 
                      (latestJob.search_report && latestJob.search_report.successful_queries) || 0,
          grants: latestJob.grants_found || 0,
          message: latestJob.error_message || ''
        });
        
        if (isRunning) {
          // If still running, check again in 2 seconds
          setTimeout(checkScraperStatus, 2000);
        } else {
          // If done, refresh data and reset running state
          setIsScraperRunning(false);
          refreshData();
        }
      }
    } catch (error) {
      console.error('Error checking scraper status:', error);
    }
  };
  
  const handleRunScraper = async () => {
    setIsScraperRunning(true);
    setScraperStatus({
      isRunning: true,
      sites: 0,
      queries: 0,
      successful: 0, 
      grants: 0,
      message: 'Initializing grant discovery...'
    });
    
    try {
      await runScraper();
      // Start polling for status
      setTimeout(checkScraperStatus, 1000);
    } catch (error) {
      console.error('Error running scraper:', error);
      setScraperStatus({
        isRunning: false,
        sites: 0,
        queries: 0,
        successful: 0,
        grants: 0,
        message: `Error: ${error.message || 'Failed to start scraper'}`
      });
      setIsScraperRunning(false);
    }
  };
  
  if (loading && !dashboardData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
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

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between md:items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Grant Management Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Overview of your grant activities and opportunities
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-3">
          <button
            onClick={handleRunScraper}
            disabled={isScraperRunning}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
          >
            {isScraperRunning ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Discovering Grants...
              </>
            ) : (
              <>
                <svg className="-ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Run Grant Scraper
              </>
            )}
          </button>
          <Link
            to="/grants"
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          >
            View All Grants
          </Link>
        </div>
      </div>

      {/* Scraper Status */}
      {isScraperRunning && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
          <div className="flex justify-between">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="animate-spin h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Discovering Grants
                </h3>
                <div className="mt-1 text-sm text-blue-700">
                  {scraperStatus.message || 'Searching for grants that match your organization profile...'}
                </div>
              </div>
            </div>
            <div className="text-right text-sm text-blue-700">
              <div><span className="font-semibold">{scraperStatus.sites}</span> sites searched</div>
              <div><span className="font-semibold">{scraperStatus.successful}/{scraperStatus.queries}</span> successful queries</div>
              <div><span className="font-semibold">{scraperStatus.grants}</span> grants found</div>
            </div>
          </div>
        </div>
      )}

      {/* Stats cards */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-primary-light rounded-md p-3">
                  <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                        {dashboardData.total_grants}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-green-100 rounded-md p-3">
                  <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                        {formatCurrency(dashboardData.potential_funding)}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-secondary-light rounded-md p-3">
                  <svg className="h-6 w-6 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                        {formatCurrency(dashboardData.won_funding)}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-accent-light rounded-md p-3">
                  <svg className="h-6 w-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        </div>
      )}
      
      {/* Charts and Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left column - Charts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status Distribution */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Grant Status Distribution</h2>
            <div className="h-64">
              <canvas id="statusChart"></canvas>
            </div>
          </div>
          
          {/* Match Score Distribution */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Match Score Distribution</h2>
            <div className="h-64">
              <canvas id="matchChart"></canvas>
            </div>
          </div>
        </div>
        
        {/* Right column - Lists */}
        <div className="lg:col-span-3 space-y-6">
          {/* Upcoming Deadlines */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Upcoming Deadlines</h2>
            </div>
            {dashboardData && dashboardData.upcoming_deadlines && dashboardData.upcoming_deadlines.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {dashboardData.upcoming_deadlines.map((grant) => (
                  <div key={grant.id} className="px-6 py-4 flex items-center">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-medium text-gray-900">
                        <Link to={`/grants/${grant.id}`} className="hover:underline">
                          {grant.title}
                        </Link>
                      </h3>
                      <div className="mt-1 flex items-center text-sm text-gray-500">
                        <span className="truncate">{grant.funder}</span>
                        <span className="mx-1">•</span>
                        <span className={getDateUrgencyClass(grant.due_date)}>
                          Due: {formatDate(grant.due_date)}
                        </span>
                      </div>
                    </div>
                    <div className="ml-6 flex-shrink-0">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusClass(grant.status)}`}>
                        {grant.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-6 py-8 text-center text-gray-500">
                <svg className="mx-auto h-10 w-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="mt-2 text-sm">No upcoming deadlines in the next 30 days</p>
              </div>
            )}
          </div>
          
          {/* Top Matching Grants */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Top Matching Grants</h2>
            </div>
            {grants.filter(g => g.match_score >= 70).length > 0 ? (
              <div className="divide-y divide-gray-200">
                {grants
                  .filter(g => g.match_score >= 70)
                  .sort((a, b) => b.match_score - a.match_score)
                  .slice(0, 5)
                  .map((grant) => (
                    <div key={grant.id} className="px-6 py-4 flex items-center">
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-medium text-gray-900">
                          <Link to={`/grants/${grant.id}`} className="hover:underline">
                            {grant.title}
                          </Link>
                        </h3>
                        <div className="mt-1 flex items-center text-sm text-gray-500">
                          <span className="truncate">{grant.funder}</span>
                          <span className="mx-1">•</span>
                          <span>{formatCurrency(grant.amount)}</span>
                        </div>
                      </div>
                      <div className="ml-6 flex-shrink-0">
                        <span className={`text-sm font-medium ${getMatchScoreClass(grant.match_score)}`}>
                          {formatMatchScore(grant.match_score)}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="px-6 py-8 text-center text-gray-500">
                <svg className="mx-auto h-10 w-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="mt-2 text-sm">No high-matching grants found</p>
                <p className="mt-1 text-xs">Run the grant scraper to find matching opportunities</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

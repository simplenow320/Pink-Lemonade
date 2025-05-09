import React, { useEffect, useState } from 'react';
import { 
  getAnalyticsOverview, 
  getAnalyticsTrends, 
  getAnalyticsCategoryComparison,
  updateAnalyticsMetrics
} from '../utils/api';
import { useNotification } from '../context/NotificationContext';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Chart from 'chart.js/auto';
import { Bar, Line, Doughnut } from 'react-chartjs-2';

const AnalyticsPage = () => {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState(null);
  const [categories, setCategories] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const { addError, addSuccess } = useNotification();

  // Define chart options
  const lineOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              if (context.dataset.label === 'Success Rate') {
                label += context.parsed.y.toFixed(1) + '%';
              } else if (context.dataset.label === 'Funding Received') {
                label += '$' + context.parsed.y.toLocaleString();
              } else {
                label += context.parsed.y;
              }
            }
            return label;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            if (this.chart.config._config.data.datasets[0].label === 'Success Rate') {
              return value + '%';
            } else if (this.chart.config._config.data.datasets[0].label === 'Funding Received') {
              return '$' + value.toLocaleString();
            }
            return value;
          }
        }
      }
    }
  };

  const barOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += context.parsed.y.toFixed(1) + '%';
            }
            return label;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return value + '%';
          }
        }
      }
    }
  };

  const doughnutOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'right',
      }
    }
  };

  // Load analytics data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch overview data
        const overviewData = await getAnalyticsOverview();
        setOverview(overviewData);
        
        // Fetch trend data for success rate
        const trendData = await getAnalyticsTrends('success_rate', 'monthly', 12);
        setTrends(trendData);
        
        // Fetch category comparison
        const categoryData = await getAnalyticsCategoryComparison();
        setCategories(categoryData);
        
      } catch (err) {
        console.error('Error loading analytics data:', err);
        addError('Failed to load analytics data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [addError]);

  // Handle refresh button click
  const handleRefreshMetrics = async () => {
    try {
      setRefreshing(true);
      await updateAnalyticsMetrics();
      
      // Reload the data
      const overviewData = await getAnalyticsOverview();
      setOverview(overviewData);
      
      const trendData = await getAnalyticsTrends('success_rate', 'monthly', 12);
      setTrends(trendData);
      
      const categoryData = await getAnalyticsCategoryComparison();
      setCategories(categoryData);
      
      addSuccess('Analytics metrics updated successfully');
      
    } catch (err) {
      console.error('Error updating metrics:', err);
      addError('Failed to update analytics metrics. Please try again later.');
    } finally {
      setRefreshing(false);
    }
  };

  // Prepare chart data
  const getSuccessRateChartData = () => {
    if (!trends || !trends.success) return null;
    
    return {
      labels: trends.labels,
      datasets: [
        {
          label: 'Success Rate',
          data: trends.data,
          fill: false,
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1
        }
      ]
    };
  };

  const getCategoryChartData = () => {
    if (!categories || !categories.success || categories.categories.length === 0) return null;
    
    return {
      labels: categories.categories,
      datasets: [
        {
          label: 'Success Rate by Category',
          data: categories.metrics.success_rates,
          backgroundColor: [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(255, 99, 255, 0.7)',
            'rgba(54, 162, 64, 0.7)'
          ],
        }
      ]
    };
  };

  const getStatusDistributionData = () => {
    if (!overview || !overview.success) return null;
    
    // Calculate percentages
    const total = overview.total_grants || 1; // Avoid division by zero
    const notStarted = total - overview.total_submitted;
    const inProgress = overview.total_submitted - overview.total_won - overview.total_declined;
    const won = overview.total_won;
    const declined = overview.total_declined;
    
    return {
      labels: ['Not Started', 'In Progress', 'Won', 'Declined'],
      datasets: [
        {
          data: [notStarted, inProgress, won, declined],
          backgroundColor: [
            'rgba(201, 203, 207, 0.7)',
            'rgba(255, 205, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(255, 99, 132, 0.7)',
          ],
        }
      ]
    };
  };

  // Render metric cards
  const renderMetricCards = () => {
    if (!overview || !overview.success) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="h-32 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-2/3 mb-2"></div>
              <div className="h-10 bg-gray-200 rounded w-1/2"></div>
            </Card>
          ))}
        </div>
      );
    }
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Success Rate */}
        <Card>
          <h3 className="text-lg font-medium text-gray-500">Success Rate</h3>
          <div className="mt-2 flex items-baseline">
            <p className="text-3xl font-semibold text-gray-900">
              {overview.overall_success_rate.toFixed(1)}%
            </p>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {overview.total_won} won out of {overview.total_submitted} submitted grants
          </p>
        </Card>
        
        {/* Total Funding Won */}
        <Card>
          <h3 className="text-lg font-medium text-gray-500">Total Funding Won</h3>
          <div className="mt-2 flex items-baseline">
            <p className="text-3xl font-semibold text-gray-900">
              ${overview.total_funding_won.toLocaleString()}
            </p>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Across {overview.total_won} successful grants
          </p>
        </Card>
        
        {/* Average Days to Decision */}
        <Card>
          <h3 className="text-lg font-medium text-gray-500">Avg. Decision Time</h3>
          <div className="mt-2 flex items-baseline">
            <p className="text-3xl font-semibold text-gray-900">
              {overview.avg_days_to_decision || 'N/A'}
            </p>
            {overview.avg_days_to_decision && (
              <p className="ml-1 text-sm text-gray-500">days</p>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            From submission to decision
          </p>
        </Card>
        
        {/* Total Grants */}
        <Card>
          <h3 className="text-lg font-medium text-gray-500">Total Grants</h3>
          <div className="mt-2 flex items-baseline">
            <p className="text-3xl font-semibold text-gray-900">
              {overview.total_grants}
            </p>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {overview.total_submitted} submitted, {overview.total_grants - overview.total_submitted} in pipeline
          </p>
        </Card>
      </div>
    );
  };

  return (
    <div>
      <PageHeader 
        title="Grant Analytics" 
        description="Track and analyze your grant success metrics and funding impact."
      >
        <button
          onClick={handleRefreshMetrics}
          disabled={refreshing}
          className="ml-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
        >
          {refreshing ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Updating...
            </>
          ) : (
            <>
              <svg className="-ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Metrics
            </>
          )}
        </button>
      </PageHeader>
      
      <div className="mt-6">
        {/* Metric Cards */}
        {renderMetricCards()}
        
        {/* Charts section */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Success Rate Trend */}
          <Card>
            <h3 className="text-lg font-medium text-gray-700 mb-4">Success Rate Trend</h3>
            {loading || !trends ? (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
              </div>
            ) : (
              <div className="h-64">
                {getSuccessRateChartData() ? (
                  <Line data={getSuccessRateChartData()} options={lineOptions} />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-gray-500">No trend data available</p>
                  </div>
                )}
              </div>
            )}
          </Card>
          
          {/* Grant Status Distribution */}
          <Card>
            <h3 className="text-lg font-medium text-gray-700 mb-4">Grant Status Distribution</h3>
            {loading || !overview ? (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
              </div>
            ) : (
              <div className="h-64">
                {getStatusDistributionData() ? (
                  <Doughnut data={getStatusDistributionData()} options={doughnutOptions} />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-gray-500">No status data available</p>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
        
        {/* Category Success Rates */}
        <div className="mt-6">
          <Card>
            <h3 className="text-lg font-medium text-gray-700 mb-4">Success Rates by Focus Area</h3>
            {loading || !categories ? (
              <div className="h-80 flex items-center justify-center">
                <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
              </div>
            ) : (
              <div className="h-80">
                {getCategoryChartData() ? (
                  <Bar data={getCategoryChartData()} options={barOptions} />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-gray-500">No category data available</p>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
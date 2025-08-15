import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

const Phase3AnalyticsDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [trendsData, setTrendsData] = useState(null);
  const [roiData, setRoiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('executive');

  useEffect(() => {
    fetchDashboardData();
    fetchTrendsData();
    fetchROIData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/phase3/analytics/dashboard');
      const data = await response.json();
      if (data.success) {
        setDashboardData(data.metrics);
      }
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrendsData = async () => {
    try {
      const response = await fetch('/api/phase3/analytics/trends?months=12');
      const data = await response.json();
      if (data.success) {
        setTrendsData(data);
      }
    } catch (error) {
      console.error('Error fetching trends:', error);
    }
  };

  const fetchROIData = async () => {
    try {
      const response = await fetch('/api/phase3/analytics/roi');
      const data = await response.json();
      if (data.success) {
        setRoiData(data);
      }
    } catch (error) {
      console.error('Error fetching ROI:', error);
    }
  };

  const MetricCard = ({ title, value, subtitle, trend, icon }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <span className="text-pink-500">{icon}</span>}
      </div>
      <div className="flex items-baseline">
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
        {trend && (
          <span className={`ml-2 text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );

  const renderExecutiveDashboard = () => {
    if (!dashboardData) return null;

    const successGauge = {
      datasets: [{
        data: [dashboardData.success_rate, 100 - dashboardData.success_rate],
        backgroundColor: ['#EC4899', '#E5E7EB'],
        borderWidth: 0
      }],
      labels: ['Success', 'Other']
    };

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Success Rate"
            value={`${dashboardData.success_rate}%`}
            subtitle="Grant win rate"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <MetricCard
            title="Total Awarded"
            value={`$${(dashboardData.total_awarded / 1000).toFixed(0)}K`}
            subtitle={`${dashboardData.awarded_count} grants won`}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <MetricCard
            title="Pipeline Value"
            value={`$${(dashboardData.pipeline_value / 1000).toFixed(0)}K`}
            subtitle={`${dashboardData.active_count} active grants`}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
          />
          <MetricCard
            title="Avg Time to Submit"
            value={`${dashboardData.avg_days_to_submit}`}
            subtitle="Days per application"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Success Rate Overview</h3>
            <div className="w-48 h-48 mx-auto">
              <Doughnut data={successGauge} options={{
                plugins: {
                  legend: { display: false },
                  tooltip: { enabled: false }
                },
                cutout: '70%'
              }} />
              <div className="text-center -mt-32">
                <p className="text-3xl font-bold text-pink-500">{dashboardData.success_rate}%</p>
                <p className="text-sm text-gray-600">Success Rate</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Awarded</span>
                <span className="font-semibold">{dashboardData.awarded_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Pending</span>
                <span className="font-semibold">{dashboardData.pending_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Active</span>
                <span className="font-semibold">{dashboardData.active_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Applications</span>
                <span className="font-semibold">{dashboardData.total_applications}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderTrendsAnalysis = () => {
    if (!trendsData || !trendsData.monthly_trends) return null;

    const months = Object.keys(trendsData.monthly_trends).sort();
    const chartData = {
      labels: months.map(m => {
        const [year, month] = m.split('-');
        return `${month}/${year.slice(2)}`;
      }),
      datasets: [
        {
          label: 'Applications',
          data: months.map(m => trendsData.monthly_trends[m].applications),
          borderColor: '#EC4899',
          backgroundColor: 'rgba(236, 72, 153, 0.1)',
          tension: 0.4
        },
        {
          label: 'Awarded',
          data: months.map(m => trendsData.monthly_trends[m].awarded),
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4
        }
      ]
    };

    const seasonalData = trendsData.seasonal_patterns ? {
      labels: Object.keys(trendsData.seasonal_patterns),
      datasets: [{
        label: 'Success Rate by Quarter',
        data: Object.values(trendsData.seasonal_patterns).map(q => q.success_rate),
        backgroundColor: ['#EC4899', '#F59E0B', '#3B82F6', '#10B981'],
        borderWidth: 0
      }]
    } : null;

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Trends</h3>
          <Line data={chartData} options={{
            responsive: true,
            plugins: {
              legend: { position: 'bottom' }
            },
            scales: {
              y: { beginAtZero: true }
            }
          }} />
        </div>

        {seasonalData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Seasonal Success Patterns</h3>
              <Bar data={seasonalData} options={{
                responsive: true,
                plugins: {
                  legend: { display: false }
                },
                scales: {
                  y: { beginAtZero: true, max: 100 }
                }
              }} />
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Growth Metrics</h3>
              {trendsData.growth_metrics && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Application Growth</span>
                    <span className={`font-semibold ${trendsData.growth_metrics.application_growth_rate > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {trendsData.growth_metrics.application_growth_rate > 0 ? '+' : ''}{trendsData.growth_metrics.application_growth_rate}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Success Rate Change</span>
                    <span className={`font-semibold ${trendsData.growth_metrics.success_rate_improvement > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {trendsData.growth_metrics.success_rate_improvement > 0 ? '+' : ''}{trendsData.growth_metrics.success_rate_improvement}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Avg Monthly Applications</span>
                    <span className="font-semibold">{trendsData.growth_metrics.average_monthly_applications}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderROIAnalysis = () => {
    if (!roiData) return null;

    const roiChart = {
      labels: ['Revenue', 'Costs'],
      datasets: [{
        data: [roiData.total_revenue, roiData.estimated_cost],
        backgroundColor: ['#10B981', '#EF4444'],
        borderWidth: 0
      }]
    };

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="ROI"
            value={`${roiData.roi_percentage}%`}
            subtitle="Return on investment"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
          />
          <MetricCard
            title="Total Revenue"
            value={`$${(roiData.total_revenue / 1000).toFixed(0)}K`}
            subtitle="From awarded grants"
          />
          <MetricCard
            title="Cost per Application"
            value={`$${roiData.cost_per_application}`}
            subtitle="Average investment"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue vs Costs</h3>
            <Bar data={roiChart} options={{
              responsive: true,
              plugins: {
                legend: { display: false }
              },
              scales: {
                y: { beginAtZero: true }
              }
            }} />
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Investment Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Hours Invested</span>
                <span className="font-semibold">{roiData.total_hours_invested} hrs</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Revenue per Success</span>
                <span className="font-semibold">${(roiData.revenue_per_success / 1000).toFixed(0)}K</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Applications Submitted</span>
                <span className="font-semibold">{roiData.applications_submitted}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Estimated Total Cost</span>
                <span className="font-semibold">${(roiData.estimated_cost / 1000).toFixed(0)}K</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Phase 3: Advanced Analytics
        </h2>
        <p className="text-gray-600">
          Comprehensive insights and performance metrics for data-driven decisions
        </p>
      </div>

      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('executive')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'executive'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Executive Dashboard
            </button>
            <button
              onClick={() => setActiveTab('trends')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'trends'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Trends Analysis
            </button>
            <button
              onClick={() => setActiveTab('roi')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'roi'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              ROI Analysis
            </button>
          </nav>
        </div>
      </div>

      {activeTab === 'executive' && renderExecutiveDashboard()}
      {activeTab === 'trends' && renderTrendsAnalysis()}
      {activeTab === 'roi' && renderROIAnalysis()}
    </div>
  );
};

export default Phase3AnalyticsDashboard;
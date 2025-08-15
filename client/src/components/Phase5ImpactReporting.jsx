import React, { useState, useEffect } from 'react';

const Phase5ImpactReporting = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [qrCode, setQrCode] = useState(null);
  const [surveyUrl, setSurveyUrl] = useState('');
  const [grants, setGrants] = useState([]);
  const [selectedGrant, setSelectedGrant] = useState(null);
  const [reports, setReports] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  
  // Form states
  const [reportData, setReportData] = useState({
    period: 'Q1 2025',
    narrative: '',
    metrics: {
      participants_served: 0,
      goals_achieved: 0,
      budget_utilized: 0
    }
  });

  useEffect(() => {
    fetchGrants();
    fetchReports();
    fetchDashboard();
  }, []);

  const fetchGrants = async () => {
    try {
      const response = await fetch('/api/phase2/applications/staged');
      const data = await response.json();
      if (data.success) {
        setGrants(data.grants || []);
      }
    } catch (error) {
      console.error('Error fetching grants:', error);
    }
  };

  const fetchReports = async () => {
    try {
      const response = await fetch('/api/phase5/reports/list');
      const data = await response.json();
      if (data.success) {
        setReports(data.reports || []);
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
    }
  };

  const fetchDashboard = async () => {
    try {
      const response = await fetch('/api/phase5/dashboard');
      const data = await response.json();
      if (data.success) {
        setDashboard(data.dashboard);
      }
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    }
  };

  const generateQRCode = async () => {
    if (!selectedGrant) {
      alert('Please select a grant first');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch('/api/phase5/qr/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_id: selectedGrant.id,
          program_name: selectedGrant.title || 'Grant Program'
        })
      });
      const data = await response.json();
      if (data.success) {
        setQrCode(data.qr_code);
        setSurveyUrl(data.survey_url);
      } else {
        alert(data.error || 'Failed to generate QR code');
      }
    } catch (error) {
      console.error('Error generating QR code:', error);
      alert('Error generating QR code');
    } finally {
      setLoading(false);
    }
  };

  const createReport = async () => {
    if (!selectedGrant) {
      alert('Please select a grant first');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch('/api/phase5/reports/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_id: selectedGrant.id,
          ...reportData
        })
      });
      const data = await response.json();
      if (data.success) {
        alert('Report created successfully!');
        fetchReports();
      } else {
        alert(data.error || 'Failed to create report');
      }
    } catch (error) {
      console.error('Error creating report:', error);
      alert('Error creating report');
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    if (!selectedGrant) {
      alert('Please select a grant first');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(`/api/phase5/metrics/aggregate/${selectedGrant.id}`);
      const data = await response.json();
      if (data.success) {
        setMetrics(data.metrics);
      } else {
        alert(data.error || 'Failed to fetch metrics');
      }
    } catch (error) {
      console.error('Error fetching metrics:', error);
      alert('Error fetching metrics');
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (reportId, format = 'pdf') => {
    setLoading(true);
    try {
      const response = await fetch(`/api/phase5/reports/export/${reportId}?format=${format}`);
      const data = await response.json();
      if (data.success) {
        alert(`Report exported successfully! Download from: ${data.download_url}`);
      } else {
        alert(data.error || 'Failed to export report');
      }
    } catch (error) {
      console.error('Error exporting report:', error);
      alert('Error exporting report');
    } finally {
      setLoading(false);
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h4 className="text-sm font-medium text-gray-500">Active Reports</h4>
          <p className="text-2xl font-bold text-gray-900">{dashboard?.active_reports || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h4 className="text-sm font-medium text-gray-500">Total Participants</h4>
          <p className="text-2xl font-bold text-gray-900">{dashboard?.total_participants || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h4 className="text-sm font-medium text-gray-500">Average Impact Score</h4>
          <p className="text-2xl font-bold text-pink-600">{dashboard?.average_impact_score || 0}/10</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Deadlines</h3>
        {dashboard?.upcoming_deadlines?.map((deadline, index) => (
          <div key={index} className="flex justify-between items-center py-3 border-b">
            <div>
              <p className="font-medium text-gray-900">{deadline.grant}</p>
              <p className="text-sm text-gray-500">Due: {new Date(deadline.deadline).toLocaleDateString()}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs ${
              deadline.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
            }`}>
              {deadline.status.replace('_', ' ')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );

  const renderReportCreator = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Create Grant Report</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Grant
            </label>
            <select
              value={selectedGrant?.id || ''}
              onChange={(e) => setSelectedGrant(grants.find(g => g.id === parseInt(e.target.value)))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
            >
              <option value="">Select a grant...</option>
              {grants.map(grant => (
                <option key={grant.id} value={grant.id}>
                  {grant.title || grant.grant_name} - {grant.funding_organization || grant.funder}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reporting Period
            </label>
            <input
              type="text"
              value={reportData.period}
              onChange={(e) => setReportData({...reportData, period: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Narrative Summary
            </label>
            <textarea
              value={reportData.narrative}
              onChange={(e) => setReportData({...reportData, narrative: e.target.value})}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
              placeholder="Describe the progress and achievements..."
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Participants Served
              </label>
              <input
                type="number"
                value={reportData.metrics.participants_served}
                onChange={(e) => setReportData({
                  ...reportData,
                  metrics: {...reportData.metrics, participants_served: parseInt(e.target.value)}
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Goals Achieved
              </label>
              <input
                type="number"
                value={reportData.metrics.goals_achieved}
                onChange={(e) => setReportData({
                  ...reportData,
                  metrics: {...reportData.metrics, goals_achieved: parseInt(e.target.value)}
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Budget Utilized (%)
              </label>
              <input
                type="number"
                value={reportData.metrics.budget_utilized}
                onChange={(e) => setReportData({
                  ...reportData,
                  metrics: {...reportData.metrics, budget_utilized: parseInt(e.target.value)}
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
              />
            </div>
          </div>

          <button
            onClick={createReport}
            disabled={loading || !selectedGrant}
            className="w-full bg-pink-500 text-white py-2 px-4 rounded-md hover:bg-pink-600 disabled:bg-gray-300"
          >
            {loading ? 'Creating...' : 'Create Report'}
          </button>
        </div>
      </div>
    </div>
  );

  const renderQRGenerator = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Generate Survey QR Code</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Grant/Program
            </label>
            <select
              value={selectedGrant?.id || ''}
              onChange={(e) => setSelectedGrant(grants.find(g => g.id === parseInt(e.target.value)))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
            >
              <option value="">Select a grant...</option>
              {grants.map(grant => (
                <option key={grant.id} value={grant.id}>
                  {grant.title || grant.grant_name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={generateQRCode}
            disabled={loading || !selectedGrant}
            className="w-full bg-pink-500 text-white py-2 px-4 rounded-md hover:bg-pink-600 disabled:bg-gray-300"
          >
            {loading ? 'Generating...' : 'Generate QR Code'}
          </button>

          {qrCode && (
            <div className="mt-6 text-center">
              <img src={qrCode} alt="Survey QR Code" className="mx-auto mb-4" />
              <p className="text-sm text-gray-600 mb-2">Survey URL:</p>
              <a href={surveyUrl} target="_blank" rel="noopener noreferrer" className="text-pink-500 hover:text-pink-600">
                {surveyUrl}
              </a>
              <div className="mt-4 space-x-2">
                <button
                  onClick={() => navigator.clipboard.writeText(surveyUrl)}
                  className="text-sm text-pink-500 hover:text-pink-600"
                >
                  Copy Link
                </button>
                <button
                  onClick={() => {
                    const a = document.createElement('a');
                    a.href = qrCode;
                    a.download = 'survey-qr-code.png';
                    a.click();
                  }}
                  className="text-sm text-pink-500 hover:text-pink-600"
                >
                  Download QR Code
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Survey Questions</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p className="font-semibold">Participant Information:</p>
              <ul className="list-disc list-inside ml-2">
                <li>Name</li>
                <li>Age</li>
                <li>Location</li>
                <li>Program Enrolled</li>
              </ul>
              <p className="font-semibold mt-2">Impact Questions (5):</p>
              <ul className="list-disc list-inside ml-2">
                <li>How has this program helped you?</li>
                <li>What specific changes have you experienced?</li>
                <li>Rate the program's impact (1-10)</li>
                <li>Would you recommend to others?</li>
                <li>Most valuable part of the program?</li>
              </ul>
              <p className="font-semibold mt-2">Improvement Questions (2):</p>
              <ul className="list-disc list-inside ml-2">
                <li>How could we better serve your needs?</li>
                <li>Who else could benefit from this program?</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderMetrics = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Impact Metrics</h3>
          <button
            onClick={fetchMetrics}
            disabled={loading || !selectedGrant}
            className="px-4 py-2 bg-pink-500 text-white rounded-md hover:bg-pink-600 disabled:bg-gray-300"
          >
            {loading ? 'Loading...' : 'Refresh Metrics'}
          </button>
        </div>

        <div className="mb-4">
          <select
            value={selectedGrant?.id || ''}
            onChange={(e) => setSelectedGrant(grants.find(g => g.id === parseInt(e.target.value)))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
          >
            <option value="">Select a grant...</option>
            {grants.map(grant => (
              <option key={grant.id} value={grant.id}>
                {grant.title || grant.grant_name}
              </option>
            ))}
          </select>
        </div>

        {metrics && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-500">Total Participants</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.total_participants}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-500">Average Rating</p>
                <p className="text-2xl font-bold text-pink-600">{metrics.average_rating}/10</p>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Key Themes</h4>
              <ul className="list-disc list-inside text-gray-700">
                {metrics.key_themes?.map((theme, index) => (
                  <li key={index}>{theme}</li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Improvement Suggestions</h4>
              <ul className="list-disc list-inside text-gray-700">
                {metrics.improvement_suggestions?.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderReportsList = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900">Grant Reports</h3>
      </div>
      <div className="divide-y">
        {reports.map((report) => (
          <div key={report.id} className="px-6 py-4 hover:bg-gray-50">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-medium text-gray-900">{report.grant_title}</h4>
                <p className="text-sm text-gray-500">Period: {report.period}</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-3 py-1 rounded-full text-xs ${
                  report.status === 'submitted' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {report.status}
                </span>
                <button
                  onClick={() => exportReport(report.id)}
                  className="text-pink-500 hover:text-pink-600"
                >
                  Export
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Phase 5: Impact Reporting & Data Collection
        </h2>
        <p className="text-gray-600">
          Comprehensive grant reporting with participant impact surveys
        </p>
      </div>

      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'create'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Create Report
            </button>
            <button
              onClick={() => setActiveTab('qr')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'qr'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              QR Survey
            </button>
            <button
              onClick={() => setActiveTab('metrics')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'metrics'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Impact Metrics
            </button>
            <button
              onClick={() => setActiveTab('reports')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'reports'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              All Reports
            </button>
          </nav>
        </div>
      </div>

      <div className="mt-6">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'create' && renderReportCreator()}
        {activeTab === 'qr' && renderQRGenerator()}
        {activeTab === 'metrics' && renderMetrics()}
        {activeTab === 'reports' && renderReportsList()}
      </div>
    </div>
  );
};

export default Phase5ImpactReporting;
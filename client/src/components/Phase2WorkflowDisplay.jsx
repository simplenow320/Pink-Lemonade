import React, { useState, useEffect } from 'react';

const Phase2WorkflowDisplay = () => {
  const [applications, setApplications] = useState({});
  const [deadlines, setDeadlines] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pipeline');

  const stageIcons = {
    discovery: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    research: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
    draft: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    review: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    submitted: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
      </svg>
    ),
    pending: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    awarded: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    rejected: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )
  };

  const priorityColors = {
    urgent: 'bg-red-100 text-red-800 border-red-300',
    high: 'bg-orange-100 text-orange-800 border-orange-300',
    medium: 'bg-blue-100 text-blue-800 border-blue-300',
    low: 'bg-green-100 text-green-800 border-green-300'
  };

  useEffect(() => {
    fetchApplications();
    fetchDeadlines();
    fetchReminders();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await fetch('/api/phase2/applications/staged');
      const data = await response.json();
      if (data.success) {
        setApplications(data.stages);
      }
    } catch (error) {
      console.error('Error fetching applications:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDeadlines = async () => {
    try {
      const response = await fetch('/api/phase2/deadlines?days=30');
      const data = await response.json();
      if (data.success) {
        setDeadlines(data.deadlines);
      }
    } catch (error) {
      console.error('Error fetching deadlines:', error);
    }
  };

  const fetchReminders = async () => {
    try {
      const response = await fetch('/api/phase2/reminders');
      const data = await response.json();
      if (data.success) {
        setReminders(data.reminders);
      }
    } catch (error) {
      console.error('Error fetching reminders:', error);
    }
  };

  const updateStage = async (appId, newStage) => {
    try {
      const response = await fetch(`/api/phase2/application/${appId}/stage`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stage: newStage })
      });
      const data = await response.json();
      if (data.success) {
        fetchApplications();
      }
    } catch (error) {
      console.error('Error updating stage:', error);
    }
  };

  const renderPipeline = () => (
    <div className="space-y-4">
      <div className="flex overflow-x-auto pb-4">
        {Object.entries(applications).map(([stage, stageData]) => (
          <div key={stage} className="flex-shrink-0 w-64 mx-2">
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-gray-500 mr-2">{stageIcons[stage]}</span>
                    <h3 className="font-semibold text-gray-900">{stageData.info?.name}</h3>
                  </div>
                  <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs">
                    {stageData.count}
                  </span>
                </div>
              </div>
              <div className="p-2 max-h-96 overflow-y-auto">
                {stageData.applications?.map((app) => (
                  <div
                    key={app.id}
                    className="p-3 mb-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => setSelectedApp(app)}
                  >
                    <h4 className="font-medium text-gray-900 text-sm mb-1">{app.title}</h4>
                    <p className="text-xs text-gray-600 mb-2">{app.funder}</p>
                    <div className="flex items-center justify-between">
                      <span className={`text-xs px-2 py-1 rounded border ${priorityColors[app.priority]}`}>
                        {app.priority}
                      </span>
                      {app.days_left !== null && (
                        <span className="text-xs text-gray-500">
                          {app.days_left} days
                        </span>
                      )}
                    </div>
                    {app.match_score > 0 && (
                      <div className="mt-2">
                        <div className="flex items-center">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-pink-500 h-2 rounded-full"
                              style={{ width: `${app.match_score}%` }}
                            />
                          </div>
                          <span className="ml-2 text-xs text-gray-600">{app.match_score}%</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderDeadlines = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Deadlines</h3>
        <div className="space-y-3">
          {deadlines.map((deadline) => (
            <div key={deadline.id} className="border-l-4 border-pink-500 pl-4 py-2">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{deadline.title}</h4>
                  <p className="text-sm text-gray-600">{deadline.funder}</p>
                  <div className="flex items-center mt-2 space-x-4">
                    <span className={`text-xs px-2 py-1 rounded border ${priorityColors[deadline.priority]}`}>
                      {deadline.priority}
                    </span>
                    <span className="text-xs text-gray-500">
                      Stage: {deadline.stage}
                    </span>
                    <span className="text-xs text-gray-500">
                      {deadline.completion_percentage}% complete
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-pink-500">{deadline.days_left}</p>
                  <p className="text-xs text-gray-500">days left</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderReminders = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Smart Reminders</h3>
        <div className="space-y-3">
          {reminders.map((reminder, index) => (
            <div key={index} className={`p-4 rounded-lg border ${
              reminder.type === 'urgent' ? 'bg-red-50 border-red-300' :
              reminder.type === 'high' ? 'bg-orange-50 border-orange-300' :
              'bg-blue-50 border-blue-300'
            }`}>
              <h4 className="font-medium text-gray-900 mb-1">{reminder.title}</h4>
              <p className="text-sm text-gray-600 mb-2">{reminder.message}</p>
              <button className="text-sm text-pink-600 hover:text-pink-700 font-medium">
                {reminder.action} →
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

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
          Phase 2: Application Workflow
        </h2>
        <p className="text-gray-600">
          Track and manage your grant applications through every stage
        </p>
      </div>

      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('pipeline')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'pipeline'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Pipeline View
            </button>
            <button
              onClick={() => setActiveTab('deadlines')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'deadlines'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Deadlines ({deadlines.length})
            </button>
            <button
              onClick={() => setActiveTab('reminders')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'reminders'
                  ? 'border-pink-500 text-pink-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Reminders ({reminders.length})
            </button>
          </nav>
        </div>
      </div>

      {activeTab === 'pipeline' && renderPipeline()}
      {activeTab === 'deadlines' && renderDeadlines()}
      {activeTab === 'reminders' && renderReminders()}

      {selectedApp && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">{selectedApp.title}</h3>
              <p className="text-sm text-gray-600 mb-4">{selectedApp.funder}</p>
              <div className="space-y-2">
                <p className="text-sm">
                  <span className="font-medium">Amount:</span> ${selectedApp.amount?.toLocaleString() || 'TBD'}
                </p>
                <p className="text-sm">
                  <span className="font-medium">Deadline:</span> {selectedApp.days_left} days remaining
                </p>
                <p className="text-sm">
                  <span className="font-medium">Match Score:</span> {selectedApp.match_score}%
                </p>
              </div>
              <div className="mt-4 flex justify-end space-x-2">
                <button
                  onClick={() => setSelectedApp(null)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                >
                  Close
                </button>
                <button
                  className="px-4 py-2 bg-pink-500 text-white rounded hover:bg-pink-600"
                >
                  View Details
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Phase2WorkflowDisplay;
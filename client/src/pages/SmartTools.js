import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const SmartTools = () => {
  const [healthStatus, setHealthStatus] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkSystemHealth = async () => {
      try {
        setLoading(true);
        
        // Check all Smart Reporting phases
        const phases = ['phase2', 'phase3', 'phase4', 'phase5', 'phase6'];
        const healthChecks = await Promise.all(
          phases.map(async (phase) => {
            try {
              const response = await fetch(`/api/smart-reporting/${phase}/health`);
              const data = await response.json();
              return { phase, status: data.success ? 'operational' : 'error', data };
            } catch (error) {
              return { phase, status: 'error', error: error.message };
            }
          })
        );
        
        const status = {};
        healthChecks.forEach(({ phase, status: phaseStatus, data }) => {
          status[phase] = { status: phaseStatus, data };
        });
        
        setHealthStatus(status);
      } catch (error) {
        console.error('Health check error:', error);
      } finally {
        setLoading(false);
      }
    };
    
    checkSystemHealth();
  }, []);

  const smartTools = [
    {
      id: 'case-support',
      name: 'Case for Support',
      description: 'Create compelling case documents that make the argument for why your organization deserves funding',
      icon: '📋',
      color: 'from-pink-500 to-pink-600',
      features: ['Professional funding documents', 'Mission-driven narratives', 'Donor-ready content'],
      endpoint: '/api/writing/case-support',
      route: '/case-support',
      phase: 'practical'
    },
    {
      id: 'impact-report',
      name: 'Impact Reports',
      description: 'Generate comprehensive reports showing your programs actual outcomes and community impact',
      icon: '📊',
      color: 'from-blue-500 to-blue-600',
      features: ['Outcome tracking', 'Visual metrics', 'Stakeholder reports'],
      endpoint: '/api/writing/impact-report',
      route: '/impact-report',
      phase: 'practical'
    },
    {
      id: 'grant-pitch',
      name: 'Grant Pitch',
      description: 'AI-powered pitch generator for presentations, emails, and verbal delivery to funders',
      icon: '🎯',
      color: 'from-green-500 to-green-600',
      features: ['Multiple formats', 'Funder-specific', 'Presentation ready'],
      endpoint: '/api/writing/grant-pitch',
      route: '/grant-pitch',
      phase: 'practical'
    },
    {
      id: 'writing-assistant',
      name: 'Writing Assistant',
      description: 'AI-powered text improvement and proposal writing help for any grant content',
      icon: '✍️',
      color: 'from-purple-500 to-purple-600',
      features: ['Text improvement', 'Professional polish', 'Content optimization'],
      endpoint: '/api/writing/improve',
      route: '/writing-assistant',
      phase: 'practical'
    }
  ];

  const getToolStatus = (tool) => {
    if (tool.phase === 'practical') return 'operational';
    return healthStatus[tool.phase]?.status || 'checking';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational': return 'text-green-600 bg-green-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'checking': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'operational': return '✅ Operational';
      case 'error': return '❌ Error';
      case 'checking': return '⏳ Checking...';
      default: return '❓ Unknown';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <motion.h1 
            className="text-4xl font-bold text-gray-900 mb-4"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            🚀 Smart Tools Dashboard
          </motion.h1>
          <motion.p 
            className="text-xl text-gray-600 max-w-3xl mx-auto"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Complete AI-powered grant management suite with automated matching, extraction, 
            writing, intelligence, and comprehensive reporting capabilities.
          </motion.p>
        </div>

        {/* System Overview */}
        <motion.div 
          className="bg-white rounded-lg shadow-md p-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-4">📝 Practical Grant Writing Tools</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-pink-500 rounded-full mr-3"></div>
                <div>
                  <div className="font-semibold text-pink-800">Ready-to-Use Tools</div>
                  <div className="text-sm text-pink-600">4 Practical Writing Tools Available</div>
                </div>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                <div>
                  <div className="font-semibold text-blue-800">Real Grant Documents</div>
                  <div className="text-sm text-blue-600">Professional, Donor-Ready Content</div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Smart Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {smartTools.map((tool, index) => {
            const status = getToolStatus(tool);
            
            return (
              <motion.div
                key={tool.id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow duration-300"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * index }}
                whileHover={{ y: -5 }}
              >
                {/* Tool Header */}
                <div className={`bg-gradient-to-r ${tool.color} p-6 text-white`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-3xl">{tool.icon}</div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
                      {getStatusText(status)}
                    </div>
                  </div>
                  <h3 className="text-xl font-bold mb-1">{tool.name}</h3>
                  <p className="text-sm opacity-90">{tool.description}</p>
                </div>

                {/* Tool Content */}
                <div className="p-6">
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Key Features:</h4>
                    <ul className="space-y-1">
                      {tool.features.map((feature, idx) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-center">
                          <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-2"></span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-2">
                    {tool.phase === 'practical' ? (
                      <a
                        href={tool.route}
                        className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 transition-colors"
                      >
                        Launch Tool
                      </a>
                    ) : (
                      <button
                        onClick={() => {
                          // Test the API endpoint
                          fetch(tool.endpoint)
                            .then(response => response.json())
                            .then(data => {
                              alert(`${tool.name} Test Result:\n${JSON.stringify(data, null, 2)}`);
                            })
                            .catch(error => {
                              alert(`${tool.name} Test Error:\n${error.message}`);
                            });
                        }}
                        className="w-full inline-flex items-center justify-center px-4 py-2 border border-orange-600 rounded-md shadow-sm text-sm font-medium text-orange-600 bg-white hover:bg-orange-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 transition-colors"
                      >
                        Test API
                      </button>
                    )}
                    
                    <button 
                      onClick={() => {
                        const docs = {
                          'case-support': 'Create professional funding documents with compelling narratives for donors and foundations',
                          'impact-report': 'Generate comprehensive reports showing program outcomes and community impact with visual metrics',
                          'grant-pitch': 'AI-powered pitch generator for presentations, emails, and verbal delivery in multiple formats',
                          'writing-assistant': 'Improve any grant content with AI-powered text enhancement and professional polish'
                        };
                        alert(`${tool.name} Documentation:\n\n${docs[tool.id]}\n\nEndpoint: ${tool.endpoint}`);
                      }}
                      className="w-full text-sm text-gray-600 hover:text-gray-800 underline transition-colors"
                    >
                      View Documentation
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Quick Actions */}
        <motion.div 
          className="mt-12 bg-white rounded-lg shadow-md p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-4">⚡ Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button 
              onClick={() => {
                // Test all Smart Reporting phases
                const phases = ['phase2', 'phase3', 'phase4', 'phase5', 'phase6'];
                phases.forEach(phase => {
                  fetch(`/api/smart-reporting/${phase}/health`)
                    .then(response => response.json())
                    .then(data => console.log(`${phase}:`, data))
                    .catch(error => console.error(`${phase} error:`, error));
                });
                alert('Running system health check - see console for results');
              }}
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
            >
              🔍 System Health Check
            </button>
            
            <button
              onClick={() => {
                fetch('/api/smart-reporting/phase5/executive-summary', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ report_title: 'Test Executive Summary' })
                })
                .then(response => response.json())
                .then(data => {
                  console.log('Executive Summary:', data);
                  alert('Executive summary generated - check console for details');
                })
                .catch(error => alert('Error: ' + error.message));
              }}
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
            >
              📋 Generate Report
            </button>
            
            <button
              onClick={() => {
                fetch('/api/smart-reporting/phase6/compliance-monitor')
                .then(response => response.json())
                .then(data => {
                  console.log('Compliance Status:', data);
                  alert(`Compliance Score: ${data.compliance_status?.overall_compliance_score || 'N/A'}% - check console for details`);
                })
                .catch(error => alert('Error: ' + error.message));
              }}
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
            >
              🛡️ Check Compliance
            </button>
            
            <Link
              to="/analytics"
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
            >
              📊 View Analytics
            </Link>
          </div>
        </motion.div>

        {/* System Information */}
        {!loading && Object.keys(healthStatus).length > 0 && (
          <motion.div 
            className="mt-8 bg-gray-800 text-white rounded-lg shadow-md p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 1.0 }}
          >
            <h2 className="text-xl font-bold mb-4">🔧 System Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(healthStatus).map(([phase, info]) => (
                <div key={phase} className="bg-gray-700 rounded p-3">
                  <div className="font-semibold text-sm">{phase.toUpperCase()}</div>
                  <div className={`text-xs ${info.status === 'operational' ? 'text-green-400' : 'text-red-400'}`}>
                    {info.status === 'operational' ? '✅ Operational' : '❌ Error'}
                  </div>
                  {info.data?.phase && (
                    <div className="text-xs text-gray-300 mt-1">{info.data.phase}</div>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default SmartTools;
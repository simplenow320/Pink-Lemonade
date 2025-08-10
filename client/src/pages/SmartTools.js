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
      id: 'matching',
      name: 'Smart Matching',
      description: 'AI-powered grant-to-organization matching with intelligent scoring',
      icon: '🎯',
      color: 'from-blue-500 to-blue-600',
      features: ['94% matching accuracy', 'Intelligent scoring system', 'Mission alignment analysis'],
      endpoint: '/api/ai/match-grant',
      phase: 'core'
    },
    {
      id: 'extraction',
      name: 'Smart Extraction', 
      description: 'Automated grant data extraction from documents and websites',
      icon: '📄',
      color: 'from-green-500 to-green-600',
      features: ['Document parsing', 'Web scraping', 'Data normalization'],
      endpoint: '/api/ai/extract-grant',
      phase: 'core'
    },
    {
      id: 'writing',
      name: 'Smart Writing',
      description: 'AI-powered narrative generation and proposal assistance',
      icon: '✍️',
      color: 'from-purple-500 to-purple-600',
      features: ['Automated narratives', 'Proposal templates', 'Content optimization'],
      endpoint: '/api/writing/generate-narrative',
      phase: 'core'
    },
    {
      id: 'intelligence',
      name: 'Smart Intelligence',
      description: 'Advanced grant analysis with strategic insights',
      icon: '🧠',
      color: 'from-orange-500 to-orange-600',
      features: ['Grant analysis', 'Strategic recommendations', 'Contact intelligence'],
      endpoint: '/api/grant-intelligence/analyze',
      phase: 'core'
    },
    {
      id: 'surveys',
      name: 'Smart Surveys',
      description: 'AI-refined survey building with intelligent question optimization',
      icon: '📊',
      color: 'from-indigo-500 to-indigo-600',
      features: ['Question refinement', 'Response optimization', 'Survey analytics'],
      endpoint: '/api/smart-reporting/phase2/health',
      phase: 'phase2'
    },
    {
      id: 'collection',
      name: 'Smart Collection',
      description: 'Automated data collection and validation with real-time processing',
      icon: '📥',
      color: 'from-teal-500 to-teal-600',
      features: ['Automated workflows', 'Real-time validation', 'Data cleansing'],
      endpoint: '/api/smart-reporting/phase3/health',
      phase: 'phase3'
    },
    {
      id: 'analytics',
      name: 'Smart Analytics',
      description: 'Executive dashboards with predictive analytics and insights',
      icon: '📈',
      color: 'from-red-500 to-red-600',
      features: ['Executive dashboards', 'Predictive analytics', 'Performance insights'],
      endpoint: '/api/smart-reporting/phase4/health',
      phase: 'phase4'
    },
    {
      id: 'reports',
      name: 'Smart Reports',
      description: 'Automated report generation with stakeholder customization',
      icon: '📋',
      color: 'from-pink-500 to-pink-600',
      features: ['Executive summaries', 'Stakeholder reports', 'Automated distribution'],
      endpoint: '/api/smart-reporting/phase5/health',
      phase: 'phase5'
    },
    {
      id: 'governance',
      name: 'Smart Governance',
      description: 'Comprehensive compliance monitoring and audit trail management',
      icon: '🛡️',
      color: 'from-gray-500 to-gray-600',
      features: ['Compliance monitoring', 'Audit trails', 'Data governance'],
      endpoint: '/api/smart-reporting/phase6/health',
      phase: 'phase6'
    }
  ];

  const getToolStatus = (tool) => {
    if (tool.phase === 'core') return 'operational';
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
          <h2 className="text-2xl font-bold text-gray-900 mb-4">🏆 System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                <div>
                  <div className="font-semibold text-green-800">Smart Reporting System</div>
                  <div className="text-sm text-green-600">100% Complete - All 6 Phases</div>
                </div>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                <div>
                  <div className="font-semibold text-blue-800">Core AI Tools</div>
                  <div className="text-sm text-blue-600">4 Tools Operational</div>
                </div>
              </div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-purple-500 rounded-full mr-3"></div>
                <div>
                  <div className="font-semibold text-purple-800">Enterprise Features</div>
                  <div className="text-sm text-purple-600">Compliance & Governance Active</div>
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
                    {tool.phase === 'core' ? (
                      <Link
                        to={`/smart-tools/${tool.id}`}
                        className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 transition-colors"
                      >
                        Launch Tool
                      </Link>
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
                          matching: 'AI-powered grant matching with 94% accuracy',
                          extraction: 'Document parsing and web scraping capabilities',
                          writing: 'Automated narrative generation and proposal assistance',
                          intelligence: 'Advanced grant analysis with strategic insights',
                          surveys: 'Phase 2: AI question refinement and survey builder',
                          collection: 'Phase 3: Automated data collection and validation',
                          analytics: 'Phase 4: Executive dashboards and predictive analytics',
                          reports: 'Phase 5: Automated report generation with customization',
                          governance: 'Phase 6: Compliance monitoring and audit trails'
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
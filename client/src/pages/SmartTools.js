import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const SmartTools = () => {
  const [healthStatus, setHealthStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [showSupportingTools, setShowSupportingTools] = useState(false);

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

  // Main featured tools - prominently displayed
  const mainTools = [
    {
      id: 'grant-pitch',
      name: 'Grant Pitch',
      description: 'AI-powered pitch generator for presentations, emails, and verbal delivery to funders',
      icon: '🎯',
      color: 'from-green-500 to-green-600',
      features: ['Multiple formats', 'Funder-specific', 'Presentation ready'],
      endpoint: '/api/writing/grant-pitch',
      route: '/grant-pitch',
      phase: 'practical',
      category: 'content'
    },
    {
      id: 'case-support',
      name: 'Case for Support',
      description: 'Create compelling case documents that make the argument for why your organization deserves funding',
      icon: '📋',
      color: 'from-pink-500 to-pink-600',
      features: ['Professional funding documents', 'Mission-driven narratives', 'Donor-ready content'],
      endpoint: '/api/writing/case-support',
      route: '/case-support',
      phase: 'practical',
      category: 'content'
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
      phase: 'practical',
      category: 'reporting'
    }
  ];
  
  // Supporting tools - in expandable section
  const supportingTools = [
    {
      id: 'writing-assistant',
      name: 'Writing Assistant',
      description: 'AI-powered text improvement and proposal writing help for any grant content',
      icon: '✍️',
      color: 'from-purple-500 to-purple-600',
      features: ['Text improvement', 'Professional polish', 'Content optimization'],
      endpoint: '/api/writing/improve',
      route: '/writing-assistant',
      phase: 'practical',
      category: 'content'
    },
    
    // Comprehensive Reporting System
    {
      id: 'executive-dashboard',
      name: 'Executive Dashboard',
      description: 'Real-time metrics display with predictive analytics and performance monitoring',
      icon: '📈',
      color: 'from-indigo-500 to-indigo-600',
      features: ['Real-time KPIs', 'Predictive forecasting', 'Custom dashboards'],
      endpoint: '/api/smart-reporting/phase4/executive-metrics',
      route: '/analytics',
      phase: 'phase4',
      category: 'reporting'
    },
    {
      id: 'data-visualization',
      name: 'Data Visualization',
      description: 'Advanced charts, graphs, and interactive visualizations for comprehensive analysis',
      icon: '📊',
      color: 'from-cyan-500 to-cyan-600',
      features: ['Interactive charts', 'Custom visualizations', 'Trend analysis'],
      endpoint: '/api/smart-reporting/phase4/data-visualization',
      route: '/analytics?view=charts',
      phase: 'phase4',
      category: 'reporting'
    },
    {
      id: 'automated-reports',
      name: 'Automated Report Generation',
      description: 'Scheduled executive summaries and stakeholder-specific reports with smart distribution',
      icon: '🤖',
      color: 'from-emerald-500 to-emerald-600',
      features: ['Automated scheduling', 'Multi-audience reports', 'Smart distribution'],
      endpoint: '/api/smart-reporting/phase5/executive-summary',
      route: '/reports/automated',
      phase: 'phase5',
      category: 'reporting'
    },
    {
      id: 'performance-tracking',
      name: 'Performance Tracking',
      description: 'Cross-tool data fusion with AI-powered insights and success prediction',
      icon: '🎯',
      color: 'from-orange-500 to-orange-600',
      features: ['Success metrics', 'AI predictions', 'Cross-tool analysis'],
      endpoint: '/api/smart-reporting/phase4/predictive-forecast',
      route: '/analytics?view=performance',
      phase: 'phase4',
      category: 'reporting'
    },
    
    // Data Collection & Validation
    {
      id: 'survey-builder',
      name: 'AI Survey Builder',
      description: 'Advanced survey generation with adaptive question refinement and conditional logic',
      icon: '📝',
      color: 'from-violet-500 to-violet-600',
      features: ['AI question generation', 'Conditional logic', 'Multi-stakeholder surveys'],
      endpoint: '/api/smart-reporting/phase2/survey-builder',
      route: '/surveys/builder',
      phase: 'phase2',
      category: 'data'
    },
    {
      id: 'data-validation',
      name: 'Data Validation Engine',
      description: 'Automated data quality checks with intelligent validation and cleansing',
      icon: '✅',
      color: 'from-teal-500 to-teal-600',
      features: ['Quality scoring', 'Automated validation', 'Data cleansing'],
      endpoint: '/api/smart-reporting/phase3/validation-engine',
      route: '/data/validation',
      phase: 'phase3',
      category: 'data'
    },
    {
      id: 'impact-measurement',
      name: 'Impact Measurement',
      description: 'AI-generated impact questions with automated scoring and trend analysis',
      icon: '🎪',
      color: 'from-rose-500 to-rose-600',
      features: ['AI impact questions', 'Automated scoring', 'Trend identification'],
      endpoint: '/api/smart-reporting/phase2/impact-questions',
      route: '/impact/measurement',
      phase: 'phase2',
      category: 'data'
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

  const renderToolCard = (tool, index) => {
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
            <Link
              to={tool.route}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 transition-colors"
            >
              Launch Tool
            </Link>
          </div>
        </div>
      </motion.div>
    );
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
            🚀 Comprehensive Smart Tools Suite
          </motion.h1>
          <motion.p 
            className="text-xl text-gray-600 max-w-3xl mx-auto"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Complete AI-powered grant management with automated matching, extraction, 
            writing intelligence, and comprehensive reporting capabilities.
          </motion.p>
        </div>

        {/* System Overview */}
        <motion.div 
          className="bg-white rounded-lg shadow-md p-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-4">📈 Comprehensive Grant Management Platform</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                <div>
                  <div className="font-semibold text-green-800">AI Writing Tools</div>
                  <div className="text-sm text-green-600">4 Professional Content Generators</div>
                </div>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                <div>
                  <div className="font-semibold text-blue-800">Reporting System</div>
                  <div className="text-sm text-blue-600">Advanced Analytics & Dashboards</div>
                </div>
              </div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-purple-500 rounded-full mr-3"></div>
                <div>
                  <div className="font-semibold text-purple-800">Data Collection</div>
                  <div className="text-sm text-purple-600">Smart Surveys & Validation</div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Main Featured Tools - Always Visible */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">🌟 Featured Smart Tools</h2>
          <p className="text-gray-600 mb-6">Essential AI-powered tools for grant success</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {mainTools.map((tool, index) => renderToolCard(tool, index))}
          </div>
        </div>

        {/* Supporting Tools - Expandable Section */}
        <div className="mb-12">
          <div 
            className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setShowSupportingTools(!showSupportingTools)}
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">🛠️ Comprehensive Supporting Tools</h2>
                <p className="text-gray-600 mt-1">
                  {supportingTools.length} additional tools for advanced reporting, analytics, and data management
                </p>
              </div>
              <div className="text-2xl">
                {showSupportingTools ? '▼' : '▶'}
              </div>
            </div>
          </div>

          {/* Expandable Content */}
          {showSupportingTools && (
            <motion.div 
              className="space-y-12 mt-8"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              transition={{ duration: 0.3 }}
            >
              {/* AI Writing & Document Generation */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center">
                  ✍️ Additional Writing Tools
                </h3>
                <p className="text-gray-600 mb-6">Professional proposal content and documentation tools</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {supportingTools
                    .filter(tool => tool.category === 'content')
                    .map((tool, index) => renderToolCard(tool, index))}
                </div>
              </div>

              {/* Comprehensive Reporting System */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center">
                  📊 Comprehensive Reporting & Analytics
                </h3>
                <p className="text-gray-600 mb-6">Advanced reporting, dashboards, and performance tracking</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {supportingTools
                    .filter(tool => tool.category === 'reporting')
                    .map((tool, index) => renderToolCard(tool, index))}
                </div>
              </div>

              {/* Data Collection & Validation */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center">
                  📝 Data Collection & Validation
                </h3>
                <p className="text-gray-600 mb-6">Advanced survey tools, data validation, and impact measurement</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {supportingTools
                    .filter(tool => tool.category === 'data')
                    .map((tool, index) => renderToolCard(tool, index))}
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SmartTools;
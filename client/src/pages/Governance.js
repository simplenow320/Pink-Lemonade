import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  Activity,
  Lock,
  Database,
  BarChart3,
  Clock,
  Users,
  Eye,
  TrendingUp,
  AlertCircle,
  Settings
} from 'lucide-react';

const Governance = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [metrics, setMetrics] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [complianceRules, setComplianceRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchGovernanceData();
  }, []);

  const fetchGovernanceData = async () => {
    try {
      setLoading(true);
      
      // Fetch governance status
      const statusResponse = await fetch('/api/governance/status');
      const statusData = await statusResponse.json();
      
      // Fetch metrics
      const metricsResponse = await fetch('/api/governance/dashboard/metrics');
      const metricsData = await metricsResponse.json();
      
      if (metricsData.success) {
        setMetrics(metricsData.data);
      }
      
      // Fetch audit logs
      const logsResponse = await fetch('/api/governance/audit-logs?limit=10');
      if (logsResponse.ok) {
        const logsData = await logsResponse.json();
        if (logsData.success) {
          setAuditLogs(logsData.data.logs || []);
        }
      }
      
      // Fetch compliance rules
      const rulesResponse = await fetch('/api/governance/compliance-rules');
      if (rulesResponse.ok) {
        const rulesData = await rulesResponse.json();
        if (rulesData.success) {
          setComplianceRules(rulesData.data.rules || []);
        }
      }
      
    } catch (err) {
      setError('Failed to load governance data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runComplianceCheck = async (ruleId) => {
    try {
      const response = await fetch(`/api/governance/compliance-check/${ruleId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      if (data.success) {
        alert(`Compliance check completed: ${data.data.status}`);
        fetchGovernanceData();
      }
    } catch (err) {
      console.error('Failed to run compliance check:', err);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'audit', label: 'Audit Trail', icon: FileText },
    { id: 'compliance', label: 'Compliance', icon: Shield },
    { id: 'policies', label: 'Data Policies', icon: Lock },
    { id: 'quality', label: 'Quality', icon: CheckCircle }
  ];

  const renderOverview = () => {
    if (!metrics) return null;
    
    return (
      <div className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Audit Logs</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.overview?.audit_logs || 0}
                </p>
              </div>
              <FileText className="w-8 h-8 text-pink-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Compliance Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {metrics.overview?.compliance_rate || 0}%
                </p>
              </div>
              <Shield className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Rules</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.overview?.compliance_rules || 0}
                </p>
              </div>
              <Settings className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Data Policies</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.overview?.data_policies || 0}
                </p>
              </div>
              <Lock className="w-8 h-8 text-purple-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Quality Score</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.overview?.average_quality_score || 0}/10
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
          </div>
        </div>

        {/* Activity Timeline */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded">
              <p className="text-2xl font-bold text-gray-900">
                {metrics.recent_activity?.last_24h || 0}
              </p>
              <p className="text-sm text-gray-600">Last 24 Hours</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <p className="text-2xl font-bold text-gray-900">
                {metrics.recent_activity?.last_7d || 0}
              </p>
              <p className="text-sm text-gray-600">Last 7 Days</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <p className="text-2xl font-bold text-gray-900">
                {metrics.recent_activity?.last_30d || 0}
              </p>
              <p className="text-sm text-gray-600">Last 30 Days</p>
            </div>
          </div>
        </div>

        {/* Compliance Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Compliance Status</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-sm">
                Compliant: {metrics.compliance_status?.compliant || 0}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-sm">
                Non-Compliant: {metrics.compliance_status?.non_compliant || 0}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              <span className="text-sm">
                Warning: {metrics.compliance_status?.warning || 0}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-gray-500" />
              <span className="text-sm">
                Unknown: {metrics.compliance_status?.unknown || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Alerts */}
        {metrics.alerts && metrics.alerts.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-red-800 mb-2">Critical Alerts</h3>
            {metrics.alerts.map((alert, index) => (
              <div key={index} className="flex items-start space-x-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                <div>
                  <p className="text-sm text-red-800">{alert.message}</p>
                  {alert.timestamp && (
                    <p className="text-xs text-red-600">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderAuditTrail = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold">Audit Trail</h3>
        <p className="text-sm text-gray-600 mt-1">Complete activity log with compliance tracking</p>
      </div>
      <div className="p-6">
        {auditLogs.length > 0 ? (
          <div className="space-y-3">
            {auditLogs.map((log, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
                <Activity className="w-5 h-5 text-gray-400 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{log.activity_type}</p>
                    <span className="text-xs text-gray-500">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{log.activity_description}</p>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-xs text-gray-500">User: {log.user_id}</span>
                    <span className="text-xs text-gray-500">Action: {log.action}</span>
                    {log.compliance_relevant && (
                      <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                        Compliance
                      </span>
                    )}
                    {log.security_relevant && (
                      <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded">
                        Security
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No audit logs available</p>
        )}
      </div>
    </div>
  );

  const renderCompliance = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold">Compliance Monitoring</h3>
        <p className="text-sm text-gray-600 mt-1">Automated compliance checks and regulatory tracking</p>
      </div>
      <div className="p-6">
        {complianceRules.length > 0 ? (
          <div className="space-y-4">
            {complianceRules.map((rule) => (
              <div key={rule.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium">{rule.rule_name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{rule.rule_description}</p>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        rule.severity_level === 'critical' ? 'bg-red-100 text-red-800' :
                        rule.severity_level === 'high' ? 'bg-orange-100 text-orange-800' :
                        rule.severity_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {rule.severity_level}
                      </span>
                      <span className="text-xs text-gray-500">
                        Category: {rule.rule_category}
                      </span>
                      <span className="text-xs text-gray-500">
                        Source: {rule.regulation_source}
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <button
                      onClick={() => runComplianceCheck(rule.id)}
                      className="px-3 py-1 bg-pink-500 text-white text-sm rounded hover:bg-pink-600"
                    >
                      Run Check
                    </button>
                    {rule.last_compliance_status && (
                      <div className="mt-2 text-center">
                        <span className={`text-xs ${
                          rule.last_compliance_status === 'compliant' ? 'text-green-600' :
                          rule.last_compliance_status === 'non_compliant' ? 'text-red-600' :
                          'text-yellow-600'
                        }`}>
                          {rule.last_compliance_status.replace('_', ' ')}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No compliance rules configured</p>
        )}
      </div>
    </div>
  );

  const renderPolicies = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold">Data Governance Policies</h3>
        <p className="text-sm text-gray-600 mt-1">Privacy, security, and retention policies</p>
      </div>
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Eye className="w-5 h-5 text-blue-500" />
              <h4 className="font-medium">Privacy Controls</h4>
            </div>
            <ul className="space-y-2">
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                GDPR Compliant
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                CCPA Compliant
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Data Minimization
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Consent Management
              </li>
            </ul>
          </div>
          
          <div className="border rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Lock className="w-5 h-5 text-purple-500" />
              <h4 className="font-medium">Security Policies</h4>
            </div>
            <ul className="space-y-2">
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                End-to-End Encryption
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Role-Based Access
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Audit Logging
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Secure Deletion
              </li>
            </ul>
          </div>
          
          <div className="border rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Database className="w-5 h-5 text-orange-500" />
              <h4 className="font-medium">Retention Policies</h4>
            </div>
            <ul className="space-y-2">
              <li className="flex items-center text-sm">
                <Clock className="w-4 h-4 text-gray-500 mr-2" />
                Financial Records: 7 years
              </li>
              <li className="flex items-center text-sm">
                <Clock className="w-4 h-4 text-gray-500 mr-2" />
                Grant Data: 5 years
              </li>
              <li className="flex items-center text-sm">
                <Clock className="w-4 h-4 text-gray-500 mr-2" />
                Audit Logs: 7 years
              </li>
              <li className="flex items-center text-sm">
                <Clock className="w-4 h-4 text-gray-500 mr-2" />
                User Data: Per request
              </li>
            </ul>
          </div>
          
          <div className="border rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Users className="w-5 h-5 text-green-500" />
              <h4 className="font-medium">Access Controls</h4>
            </div>
            <ul className="space-y-2">
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Multi-Factor Auth
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Least Privilege
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Regular Reviews
              </li>
              <li className="flex items-center text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Session Management
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  const renderQuality = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold">Quality Assessment</h3>
        <p className="text-sm text-gray-600 mt-1">Data and report quality monitoring</p>
      </div>
      <div className="p-6">
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="relative inline-flex items-center justify-center">
                <svg className="w-20 h-20 transform -rotate-90">
                  <circle cx="40" cy="40" r="36" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                  <circle cx="40" cy="40" r="36" stroke="#10b981" strokeWidth="8" fill="none"
                    strokeDasharray={`${2 * Math.PI * 36 * 0.85} ${2 * Math.PI * 36}`}
                    strokeLinecap="round" />
                </svg>
                <span className="absolute text-lg font-bold">8.5</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Accuracy</p>
            </div>
            
            <div className="text-center">
              <div className="relative inline-flex items-center justify-center">
                <svg className="w-20 h-20 transform -rotate-90">
                  <circle cx="40" cy="40" r="36" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                  <circle cx="40" cy="40" r="36" stroke="#3b82f6" strokeWidth="8" fill="none"
                    strokeDasharray={`${2 * Math.PI * 36 * 0.90} ${2 * Math.PI * 36}`}
                    strokeLinecap="round" />
                </svg>
                <span className="absolute text-lg font-bold">9.0</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Completeness</p>
            </div>
            
            <div className="text-center">
              <div className="relative inline-flex items-center justify-center">
                <svg className="w-20 h-20 transform -rotate-90">
                  <circle cx="40" cy="40" r="36" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                  <circle cx="40" cy="40" r="36" stroke="#8b5cf6" strokeWidth="8" fill="none"
                    strokeDasharray={`${2 * Math.PI * 36 * 0.88} ${2 * Math.PI * 36}`}
                    strokeLinecap="round" />
                </svg>
                <span className="absolute text-lg font-bold">8.8</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Consistency</p>
            </div>
            
            <div className="text-center">
              <div className="relative inline-flex items-center justify-center">
                <svg className="w-20 h-20 transform -rotate-90">
                  <circle cx="40" cy="40" r="36" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                  <circle cx="40" cy="40" r="36" stroke="#f59e0b" strokeWidth="8" fill="none"
                    strokeDasharray={`${2 * Math.PI * 36 * 0.92} ${2 * Math.PI * 36}`}
                    strokeLinecap="round" />
                </svg>
                <span className="absolute text-lg font-bold">9.2</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Timeliness</p>
            </div>
            
            <div className="text-center">
              <div className="relative inline-flex items-center justify-center">
                <svg className="w-20 h-20 transform -rotate-90">
                  <circle cx="40" cy="40" r="36" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                  <circle cx="40" cy="40" r="36" stroke="#ec4899" strokeWidth="8" fill="none"
                    strokeDasharray={`${2 * Math.PI * 36 * 0.87} ${2 * Math.PI * 36}`}
                    strokeLinecap="round" />
                </svg>
                <span className="absolute text-lg font-bold">8.7</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">Relevance</p>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium mb-3">Recent Quality Assessments</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <p className="text-sm font-medium">Grant Report Q4 2024</p>
                  <p className="text-xs text-gray-600">Overall Score: 8.9/10</p>
                </div>
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <p className="text-sm font-medium">Financial Data Import</p>
                  <p className="text-xs text-gray-600">Overall Score: 9.1/10</p>
                </div>
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <p className="text-sm font-medium">Impact Assessment Report</p>
                  <p className="text-xs text-gray-600">Overall Score: 8.5/10</p>
                </div>
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Governance & Compliance</h1>
        <p className="text-gray-600 mt-2">
          Phase 6: Enterprise-grade compliance monitoring and data governance
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm
                  ${activeTab === tab.id
                    ? 'border-pink-500 text-pink-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      <div className="mt-6">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'audit' && renderAuditTrail()}
        {activeTab === 'compliance' && renderCompliance()}
        {activeTab === 'policies' && renderPolicies()}
        {activeTab === 'quality' && renderQuality()}
      </div>
    </div>
  );
};

export default Governance;
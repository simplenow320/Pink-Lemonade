// GrantFlow React Application - No JSX Version
console.log('Loading GrantFlow application...');

// Utility functions
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
}

function formatCurrency(amount) {
  if (!amount && amount !== 0) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
}

// Main App Component
function GrantFlowApp() {
  const [grants, setGrants] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [stats, setStats] = React.useState({
    total_grants: 0,
    active_applications: 0,
    grants_won: 0,
    total_funding: 0
  });
  const [hasApiKey, setHasApiKey] = React.useState(false);

  // Load data on component mount
  React.useEffect(() => {
    loadGrants();
    loadStats();
    checkApiKey();
  }, []);

  const loadGrants = async () => {
    try {
      const response = await fetch('/api/grants');
      if (response.ok) {
        const data = await response.json();
        setGrants(data.grants || []);
      }
    } catch (error) {
      console.error('Error loading grants:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/analytics/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const checkApiKey = async () => {
    try {
      const response = await fetch('/api/ai/status');
      if (response.ok) {
        const data = await response.json();
        console.log('API status response:', data);
        // Check for both possible property names
        const hasKey = data.has_api_key || data.api_key_configured || false;
        console.log('API key available:', hasKey);
        setHasApiKey(hasKey);
      }
    } catch (error) {
      console.error('Error checking API key:', error);
    }
  };

  const handleDiscoverGrants = async (event) => {
    console.log('Discover Grants button clicked!');
    console.log('Has API Key:', hasApiKey);
    console.log('Loading state:', loading);
    
    // Prevent any default behavior
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    
    if (!hasApiKey) {
      alert('OpenAI API Key required for grant discovery. Please add your API key in settings.');
      return;
    }

    if (loading) {
      console.log('Already loading, ignoring click');
      return;
    }

    setLoading(true);
    console.log('Starting grant discovery...');
    
    try {
      const response = await fetch('/api/scraper/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      console.log('API Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('API Response data:', data);
        alert(`Successfully discovered ${data.grants_found || 0} new grants!`);
        loadGrants();
        loadStats();
      } else {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        throw new Error(`Failed to discover grants: ${response.status}`);
      }
    } catch (error) {
      console.error('Error discovering grants:', error);
      alert(`Failed to discover grants: ${error.message}. Please try again.`);
    } finally {
      setLoading(false);
      console.log('Grant discovery completed');
    }
  };

  // Create hero section
  const heroSection = React.createElement('div', {
    className: 'welcome-hero'
  }, 
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'hero-content-centered' },
        React.createElement('h1', { className: 'hero-title' }, 'GrantFlow'),
        React.createElement('p', { className: 'hero-subtitle' }, 
          'AI-Powered Grant Discovery & Management for Nonprofits'
        ),
        React.createElement('div', { className: 'hero-actions' },
          React.createElement('button', {
            className: `btn btn-primary ${loading ? 'disabled' : ''}`,
            onClick: handleDiscoverGrants,
            disabled: loading,
            style: { 
              cursor: loading ? 'not-allowed' : 'pointer',
              pointerEvents: 'auto',
              zIndex: 10 
            }
          }, loading ? 'Discovering...' : 'Discover Grants'),
          React.createElement('button', {
            className: 'btn btn-outline',
            onClick: () => window.location.href = '/profile'
          }, 'Manage Profile')
        ),
        
        // Progress section
        React.createElement('div', { className: 'discovery-progress' },
          React.createElement('div', { className: 'progress-info' },
            React.createElement('p', null, 
              `${grants.length} grants discovered • ${stats.active_applications} active applications`
            ),
            React.createElement('div', { className: 'progress-stats' },
              React.createElement('span', null, `Total Funding: ${formatCurrency(stats.total_funding)}`),
              React.createElement('span', null, `Success Rate: ${stats.total_grants > 0 ? Math.round((stats.grants_won / stats.total_grants) * 100) : 0}%`)
            )
          )
        )
      )
    )
  );

  // Create stats section
  const statsSection = React.createElement('div', { className: 'container' },
    React.createElement('div', { className: 'dashboard-stats' },
      React.createElement('div', { className: 'stat-card' },
        React.createElement('div', { className: 'stat-icon' }, '📊'),
        React.createElement('div', { className: 'stat-title' }, 'Total Grants'),
        React.createElement('div', { className: 'stat-value' }, stats.total_grants)
      ),
      React.createElement('div', { className: 'stat-card' },
        React.createElement('div', { className: 'stat-icon' }, '⚡'),
        React.createElement('div', { className: 'stat-title' }, 'Active Applications'),
        React.createElement('div', { className: 'stat-value' }, stats.active_applications)
      ),
      React.createElement('div', { className: 'stat-card' },
        React.createElement('div', { className: 'stat-icon' }, '🏆'),
        React.createElement('div', { className: 'stat-title' }, 'Grants Won'),
        React.createElement('div', { className: 'stat-value' }, stats.grants_won)
      ),
      React.createElement('div', { className: 'stat-card' },
        React.createElement('div', { className: 'stat-icon' }, '💰'),
        React.createElement('div', { className: 'stat-title' }, 'Total Funding'),
        React.createElement('div', { className: 'stat-value' }, formatCurrency(stats.total_funding))
      )
    )
  );

  // Create recent grants section
  const recentGrantsSection = grants.length > 0 ? 
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'dashboard-section' },
        React.createElement('div', { className: 'section-header' },
          React.createElement('h2', null, 'Recent Grant Discoveries'),
          React.createElement('button', {
            className: 'btn btn-primary',
            onClick: () => window.location.href = '/grants'
          }, 'View All Grants')
        ),
        React.createElement('div', { className: 'card' },
          React.createElement('div', { className: 'table-responsive' },
            React.createElement('table', { className: 'table' },
              React.createElement('thead', null,
                React.createElement('tr', null,
                  React.createElement('th', null, 'Grant Title'),
                  React.createElement('th', null, 'Funder'),
                  React.createElement('th', null, 'Amount'),
                  React.createElement('th', null, 'Due Date'),
                  React.createElement('th', null, 'Status'),
                  React.createElement('th', null, 'Match Score')
                )
              ),
              React.createElement('tbody', null,
                grants.slice(0, 5).map(grant => 
                  React.createElement('tr', { key: grant.id },
                    React.createElement('td', null,
                      React.createElement('div', { className: 'grant-title' }, grant.title),
                      grant.description ? React.createElement('div', { 
                        className: 'grant-description-small' 
                      }, grant.description.substring(0, 100) + '...') : null
                    ),
                    React.createElement('td', null, grant.funder || 'Unknown'),
                    React.createElement('td', null, formatCurrency(grant.amount)),
                    React.createElement('td', null, grant.due_date ? formatDate(grant.due_date) : 'N/A'),
                    React.createElement('td', null,
                      React.createElement('span', {
                        className: `badge status-${(grant.status || 'not-started').toLowerCase().replace(/\s+/g, '-')}`
                      }, grant.status || 'Not Started')
                    ),
                    React.createElement('td', null,
                      React.createElement('div', { className: 'match-score-indicator' },
                        React.createElement('div', { className: 'match-score-bar' },
                          React.createElement('div', {
                            className: `match-score-bar ${
                              grant.match_score >= 80 ? 'high' : 
                              grant.match_score >= 50 ? 'medium' : 'low'
                            }`,
                            style: { width: `${grant.match_score || 0}%` }
                          })
                        ),
                        React.createElement('span', { className: 'match-score-value' }, 
                          `${grant.match_score || 0}%`
                        )
                      )
                    )
                  )
                )
              )
            )
          )
        )
      )
    ) : 
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'card' },
        React.createElement('div', { className: 'card-body no-grants-message' },
          React.createElement('h3', null, 'No Grants Discovered Yet'),
          React.createElement('p', null, 'Use the "Discover Grants" button above to find funding opportunities that match your organization\'s mission.'),
          !hasApiKey ? React.createElement('div', { className: 'alert alert-warning' },
            React.createElement('strong', null, 'OpenAI API Key Required: '),
            'To enable AI-powered grant discovery, please add your OpenAI API key in the settings.'
          ) : null
        )
      )
    );

  // Render complete app
  return React.createElement('div', null,
    heroSection,
    statsSection,
    recentGrantsSection
  );
}

// Render the application
console.log('Rendering GrantFlow application...');
console.log('React available:', typeof React !== 'undefined');
console.log('ReactDOM available:', typeof ReactDOM !== 'undefined');

try {
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    throw new Error('Root element not found');
  }
  
  ReactDOM.render(React.createElement(GrantFlowApp), rootElement);
  console.log('GrantFlow application rendered successfully!');
} catch (error) {
  console.error('Failed to render GrantFlow application:', error);
  
  // Fallback content
  const rootElement = document.getElementById('root');
  if (rootElement) {
    rootElement.innerHTML = `
      <div style="padding: 2rem; text-align: center; background: white; margin: 2rem; border-radius: 8px; box-shadow: 0 2px 10px r#e5e7eb;">
        <h1 style="color: #dc3545; margin-bottom: 1rem;">GrantFlow Loading Error</h1>
        <p style="color: #6c757d; margin-bottom: 1rem;">There was an issue loading the application.</p>
        <p style="color: #6c757d; font-size: 0.9rem;">Error: ${error.message}</p>
        <button onclick="window.location.reload()" style="background: #007bff; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; margin-top: 1rem;">Reload Page</button>
      </div>
    `;
  }
}
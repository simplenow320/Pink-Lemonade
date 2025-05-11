// React components for GrantFlow application

// Root component for the GrantFlow application
function App() {
  const [page, setPage] = React.useState('dashboard');
  const [loading, setLoading] = React.useState(false);
  const [organization, setOrganization] = React.useState(null);
  const [grants, setGrants] = React.useState([]);
  const [dashboardData, setDashboardData] = React.useState(null);
  const [hasApiKey, setHasApiKey] = React.useState(false);

  // Check if API key is configured
  React.useEffect(() => {
    fetch('/api/ai/status')
      .then(response => response.json())
      .then(data => {
        setHasApiKey(data.api_key_configured);
      })
      .catch(error => {
        console.error('Error checking API status:', error);
        setHasApiKey(false);
      });
  }, []);

  // Fetch organization data
  React.useEffect(() => {
    setLoading(true);
    fetch('/api/organization')
      .then(response => response.json())
      .then(data => {
        setOrganization(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching organization:', error);
        setLoading(false);
      });
  }, []);

  // Fetch grants data when viewing grants list
  React.useEffect(() => {
    if (page === 'grants') {
      setLoading(true);
      fetch('/api/grants')
        .then(response => response.json())
        .then(data => {
          setGrants(data);
          setLoading(false);
        })
        .catch(error => {
          console.error('Error fetching grants:', error);
          setLoading(false);
        });
    }
  }, [page]);

  // Fetch dashboard data when viewing dashboard
  React.useEffect(() => {
    if (page === 'dashboard') {
      setLoading(true);
      fetch('/api/grants/dashboard')
        .then(response => response.json())
        .then(data => {
          setDashboardData(data);
          setLoading(false);
        })
        .catch(error => {
          console.error('Error fetching dashboard data:', error);
          setLoading(false);
        });
    }
  }, [page]);

  // Handle page navigation
  const navigateTo = (pageName) => {
    setPage(pageName);
  };

  // Render current page based on state
  const renderPage = () => {
    if (loading) {
      return <LoadingIndicator />;
    }

    switch(page) {
      case 'dashboard':
        return <Dashboard data={dashboardData} hasApiKey={hasApiKey} />;
      case 'grants':
        return <GrantsList grants={grants} hasApiKey={hasApiKey} />;
      case 'organization':
        return <OrganizationProfile organization={organization} />;
      case 'scraper':
        // Redirect to the standalone scraper page
        window.location.href = '/scraper';
        return <LoadingIndicator />;
      default:
        return <Dashboard data={dashboardData} hasApiKey={hasApiKey} />;
    }
  };

  return (
    <div className="app-container">
      <TopNavbar 
        currentPage={page} 
        onNavigate={navigateTo} 
        organization={organization}
      />
      <main className="main-content-full">
        <Header page={page} organization={organization} />
        {renderPage()}
      </main>
    </div>
  );
}

// TopNavbar component for navigation (replaces Sidebar)
function TopNavbar({ currentPage, onNavigate, organization }) {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  return (
    <header className="top-navbar">
      <div className="navbar-container">
        <div className="navbar-logo">
          <h1>GrantFlow</h1>
        </div>
        
        {/* Desktop navigation */}
        <nav className="desktop-nav">
          <ul>
            <li className={currentPage === 'dashboard' ? 'active' : ''}>
              <a href="#" onClick={() => onNavigate('dashboard')}>
                <span className="icon">📊</span>
                <span>Dashboard</span>
              </a>
            </li>
            <li className={currentPage === 'grants' ? 'active' : ''}>
              <a href="#" onClick={() => onNavigate('grants')}>
                <span className="icon">📝</span>
                <span>Grants</span>
              </a>
            </li>
            <li className={currentPage === 'organization' ? 'active' : ''}>
              <a href="#" onClick={() => onNavigate('organization')}>
                <span className="icon">🏢</span>
                <span>Organization</span>
              </a>
            </li>
            <li className={currentPage === 'scraper' ? 'active' : ''}>
              <a href="/scraper" target="_blank">
                <span className="icon">🔍</span>
                <span>Grant Scraper</span>
              </a>
            </li>
          </ul>
        </nav>
        
        {/* Mobile menu button */}
        <button className="mobile-menu-button" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          <span className="icon">{isMenuOpen ? '✕' : '☰'}</span>
        </button>
      </div>
      
      {/* Mobile navigation */}
      {isMenuOpen && (
        <nav className="mobile-nav">
          <ul>
            <li className={currentPage === 'dashboard' ? 'active' : ''}>
              <a href="#" onClick={() => { onNavigate('dashboard'); setIsMenuOpen(false); }}>
                <span className="icon">📊</span>
                <span>Dashboard</span>
              </a>
            </li>
            <li className={currentPage === 'grants' ? 'active' : ''}>
              <a href="#" onClick={() => { onNavigate('grants'); setIsMenuOpen(false); }}>
                <span className="icon">📝</span>
                <span>Grants</span>
              </a>
            </li>
            <li className={currentPage === 'organization' ? 'active' : ''}>
              <a href="#" onClick={() => { onNavigate('organization'); setIsMenuOpen(false); }}>
                <span className="icon">🏢</span>
                <span>Organization</span>
              </a>
            </li>
            <li className={currentPage === 'scraper' ? 'active' : ''}>
              <a href="/scraper" target="_blank">
                <span className="icon">🔍</span>
                <span>Grant Scraper</span>
              </a>
            </li>
          </ul>
        </nav>
      )}
    </header>
  );
}

// Header component for current page
function Header({ page, organization }) {
  const getPageTitle = () => {
    switch(page) {
      case 'dashboard': return 'Dashboard';
      case 'grants': return 'Grant Management';
      case 'organization': return 'Organization Profile';
      case 'scraper': return 'Grant Scraper';
      default: return 'Dashboard';
    }
  };
  
  return (
    <header className="page-header">
      <h1>{getPageTitle()}</h1>
      <div className="header-actions">
        {/* Add action buttons as needed */}
      </div>
    </header>
  );
}

// Loading indicator component
function LoadingIndicator() {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>Loading...</p>
    </div>
  );
}

// Dashboard component
function Dashboard({ data, hasApiKey }) {
  if (!data) {
    return (
      <div className="container">
        <div className="card">
          <div className="card-body">
            <h2>Welcome to GrantFlow</h2>
            <p>Loading dashboard data...</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container">
      {!hasApiKey && (
        <div className="alert alert-warning">
          <strong>OpenAI API Key Required:</strong> To enable AI-powered features like grant matching and narrative generation, please add your OpenAI API key in the settings.
        </div>
      )}
      
      <div className="welcome-hero">
        <div className="hero-content">
          <h1 className="hero-title">Discover & Manage Grants Efficiently</h1>
          <p className="hero-subtitle">
            GrantFlow helps you find the perfect funding opportunities for your nonprofit organization with AI-powered matching and automated discovery.
          </p>
          <div className="hero-actions">
            <a href="#" className="btn btn-primary">Discover Grants</a>
            <a href="#" className="btn btn-outline">Learn More</a>
          </div>
        </div>
        <div className="hero-image">
          <div className="hero-image-container">
            <svg width="400" height="300" viewBox="0 0 400 300" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="400" height="300" rx="20" fill="#FFFFFF"/>
              <circle cx="200" cy="150" r="80" fill="#FFD380"/>
              <path d="M260 150C260 183.137 233.137 210 200 210C166.863 210 140 183.137 140 150C140 116.863 166.863 90 200 90C233.137 90 260 116.863 260 150Z" fill="#F8B049"/>
              <rect x="180" y="130" width="120" height="20" rx="10" fill="#FFFFFF"/>
              <rect x="200" y="160" width="80" height="20" rx="10" fill="#FFFFFF"/>
              <path d="M140 180C140 146.863 166.863 120 200 120" stroke="#FFFFFF" strokeWidth="8" strokeLinecap="round"/>
            </svg>
          </div>
        </div>
      </div>
      
      <div className="dashboard-stats">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-title">Total Grants</div>
          <div className="stat-value">{data.total_grants || 0}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-title">Potential Funding</div>
          <div className="stat-value">{formatCurrency(data.potential_funding || 0)}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🏆</div>
          <div className="stat-title">Won Funding</div>
          <div className="stat-value">{formatCurrency(data.won_funding || 0)}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">✏️</div>
          <div className="stat-title">Active Applications</div>
          <div className="stat-value">
            {(data.status_counts && (data.status_counts['Not Started'] + data.status_counts['In Progress'])) || 0}
          </div>
        </div>
      </div>
      
      <div className="dashboard-section">
        <h2>Upcoming Deadlines</h2>
        <div className="card">
          <div className="card-body">
            {data.upcoming_deadlines && data.upcoming_deadlines.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>Grant</th>
                    <th>Funder</th>
                    <th>Amount</th>
                    <th>Due Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.upcoming_deadlines.map(grant => (
                    <tr key={grant.id}>
                      <td>{grant.title}</td>
                      <td>{grant.funder}</td>
                      <td>{formatCurrency(grant.amount)}</td>
                      <td>{formatDate(new Date(grant.due_date))}</td>
                      <td>
                        <span className={`badge status-${grant.status.toLowerCase().replace(/\s+/g, '-')}`}>
                          {grant.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No upcoming deadlines</p>
            )}
          </div>
        </div>
      </div>
      
      <div className="dashboard-section">
        <h2>Grants by Status</h2>
        <div className="card">
          <div className="card-body">
            <div className="status-chart">
              {/* Status chart would go here - simplified for now */}
              <div className="status-bars">
                {data.status_counts && Object.entries(data.status_counts).map(([status, count]) => (
                  <div key={status} className="status-bar-container">
                    <div className="status-bar-label">{status}</div>
                    <div className="status-bar">
                      <div 
                        className={`status-bar-fill status-${status.toLowerCase().replace(/\s+/g, '-')}`}
                        style={{width: `${(count / data.total_grants) * 100}%`}}
                      ></div>
                    </div>
                    <div className="status-bar-value">{count}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="dashboard-section">
        <div className="section-header">
          <h2>Recently Discovered Grants</h2>
          <span className="badge bg-primary">Auto-updated daily</span>
        </div>
        <div className="card">
          <div className="card-body">
            {data.recently_discovered && data.recently_discovered.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>Grant</th>
                    <th>Funder</th>
                    <th>Amount</th>
                    <th>Match Score</th>
                    <th>Discovery Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recently_discovered.map(grant => (
                    <tr key={grant.id}>
                      <td>{grant.title}</td>
                      <td>{grant.funder}</td>
                      <td>{formatCurrency(grant.amount)}</td>
                      <td>
                        <div className="match-score-indicator">
                          <div 
                            className={`match-score-bar ${
                              grant.match_score >= 80 ? 'high' : 
                              grant.match_score >= 50 ? 'medium' : 'low'}`
                            }
                            style={{width: `${grant.match_score}%`}}
                          ></div>
                          <span className="match-score-value">{grant.match_score}%</span>
                        </div>
                      </td>
                      <td>{formatDate(new Date(grant.created_at))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No grants have been discovered in the last 7 days. Use the Grant Scraper to find more opportunities.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Grants list component
function GrantsList({ grants, hasApiKey }) {
  if (!grants || grants.length === 0) {
    return (
      <div className="container">
        <div className="card">
          <div className="card-body">
            <h2>No Grants Found</h2>
            <p>No grant data is available. Add your first grant to get started.</p>
            <button className="btn btn-primary">Add Grant</button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container">
      {!hasApiKey && (
        <div className="alert alert-warning">
          <strong>OpenAI API Key Required:</strong> To enable AI-powered features like grant matching and narrative generation, please add your OpenAI API key in the settings.
        </div>
      )}
      
      <div className="grants-actions">
        <button className="btn btn-primary">Add Grant</button>
        <div className="grants-filters">
          {/* Filters would go here */}
        </div>
      </div>
      
      <div className="grants-list">
        <div className="card">
          <div className="card-body">
            <table className="table">
              <thead>
                <tr>
                  <th>Grant</th>
                  <th>Funder</th>
                  <th>Amount</th>
                  <th>Due Date</th>
                  <th>Status</th>
                  <th>Match Score</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {grants.map(grant => (
                  <tr key={grant.id}>
                    <td>{grant.title}</td>
                    <td>{grant.funder}</td>
                    <td>{formatCurrency(grant.amount)}</td>
                    <td>{formatDate(new Date(grant.due_date))}</td>
                    <td>
                      <span className={`badge status-${grant.status.toLowerCase().replace(/\s+/g, '-')}`}>
                        {grant.status}
                      </span>
                    </td>
                    <td>
                      <div className="match-score">
                        <div className="progress-bar">
                          <div 
                            className={`progress-bar-fill ${grant.match_score >= 80 ? 'high' : grant.match_score >= 50 ? 'medium' : 'low'}`}
                            style={{width: `${grant.match_score}%`}}
                          ></div>
                        </div>
                        <span className={`match-score-value ${grant.match_score >= 80 ? 'match-high' : grant.match_score >= 50 ? 'match-medium' : 'match-low'}`}>
                          {grant.match_score}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className="actions">
                        <button className="btn btn-sm btn-outline">View</button>
                        <button className="btn btn-sm btn-outline">Edit</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

// Organization Profile component
function OrganizationProfile({ organization }) {
  if (!organization) {
    return (
      <div className="container">
        <div className="card">
          <div className="card-body">
            <h2>Organization Profile</h2>
            <p>Loading organization data...</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container">
      <div className="card">
        <div className="card-header">
          <h2>Organization Details</h2>
          <button className="btn btn-primary">Edit Profile</button>
        </div>
        <div className="card-body">
          <div className="profile-section">
            <h3>Basic Information</h3>
            <div className="profile-field">
              <div className="profile-label">Name</div>
              <div className="profile-value">{organization.name}</div>
            </div>
            <div className="profile-field">
              <div className="profile-label">Website</div>
              <div className="profile-value">
                {organization.website ? (
                  <a href={organization.website} target="_blank" rel="noopener noreferrer">
                    {organization.website}
                  </a>
                ) : (
                  'Not provided'
                )}
              </div>
            </div>
            <div className="profile-field">
              <div className="profile-label">Founded</div>
              <div className="profile-value">{organization.founding_year || 'Not provided'}</div>
            </div>
          </div>
          
          <div className="profile-section">
            <h3>Mission</h3>
            <div className="profile-value mission-statement">
              {organization.mission || 'No mission statement provided.'}
            </div>
          </div>
          
          <div className="profile-section">
            <h3>Focus Areas</h3>
            <div className="profile-value">
              {organization.focus_areas && organization.focus_areas.length > 0 ? (
                <div className="focus-areas">
                  {organization.focus_areas.map((area, index) => (
                    <span key={index} className="badge badge-primary">{area}</span>
                  ))}
                </div>
              ) : (
                'No focus areas provided.'
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Scraper Settings component
function ScraperSettings({ hasApiKey }) {
  const [sources, setSources] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [history, setHistory] = React.useState([]);
  const [isRunning, setIsRunning] = React.useState(false);
  const [runStatus, setRunStatus] = React.useState(null);
  
  // Function to fetch sources and history data
  const fetchData = () => {
    setLoading(true);
    
    // Fetch scraper sources
    fetch('/api/scraper/sources')
      .then(response => response.json())
      .then(data => {
        setSources(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching scraper sources:', error);
        setLoading(false);
      });
    
    // Fetch scraper history
    fetch('/api/scraper/history')
      .then(response => response.json())
      .then(data => {
        setHistory(data);
      })
      .catch(error => {
        console.error('Error fetching scraper history:', error);
      });
  };
  
  // Initial data load
  React.useEffect(() => {
    fetchData();
  }, []);
  
  // Function to run the scraper
  const runScraper = () => {
    if (isRunning) return;
    
    setIsRunning(true);
    setRunStatus({ status: 'running', message: 'Scraping job started...' });
    
    fetch('/api/scraper/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then(response => response.json())
      .then(data => {
        setIsRunning(false);
        setRunStatus({ 
          status: 'success', 
          message: `Scraping complete! Found ${data.results.grants_found} grants, added ${data.results.grants_added} new grants.` 
        });
        // Refresh the data
        fetchData();
      })
      .catch(error => {
        console.error('Error running scraper:', error);
        setIsRunning(false);
        setRunStatus({ status: 'error', message: 'Error running scraper. Please try again.' });
      });
  };
  
  return (
    <div className="container">
      {!hasApiKey && (
        <div className="alert alert-warning">
          <strong>OpenAI API Key Required:</strong> The grant scraper requires an OpenAI API key to extract and analyze grant data. Please add your key in the settings.
        </div>
      )}
      
      {runStatus && (
        <div className={`alert ${runStatus.status === 'success' ? 'alert-success' : runStatus.status === 'error' ? 'alert-danger' : 'alert-info'}`}>
          {runStatus.message}
        </div>
      )}
      
      <div className="card mb-4">
        <div className="card-header bg-primary text-white">
          <h2>Automated Scraping Schedule</h2>
        </div>
        <div className="card-body">
          <div className="automation-info">
            <div className="automation-status">
              <span className="badge bg-success">Active</span>
              <h3>Daily Scraping at Midnight EST</h3>
            </div>
            <p>The grant scraper automatically runs every day at midnight EST to find new grant opportunities that match your organization's profile.</p>
            <p>Last run: {history.length > 0 ? formatDate(new Date(history[0].end_time)) : 'Never'}</p>
            <p>Next run: Tonight at midnight EST</p>
            <div className="automation-actions">
              <button className="btn btn-primary" onClick={runScraper} disabled={isRunning}>
                {isRunning ? 'Running Scraper...' : 'Run Manual Scrape Now'}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="card">
        <div className="card-header">
          <h2>Grant Sources</h2>
          <button className="btn btn-primary">Add Source</button>
        </div>
        <div className="card-body">
          {loading ? (
            <LoadingIndicator />
          ) : sources.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>URL</th>
                  <th>Status</th>
                  <th>Last Scraped</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sources.map(source => (
                  <tr key={source.id}>
                    <td>{source.name}</td>
                    <td>
                      <a href={source.url} target="_blank" rel="noopener noreferrer">
                        {source.url}
                      </a>
                    </td>
                    <td>
                      <span className={`badge ${source.is_active ? 'badge-success' : 'badge-secondary'}`}>
                        {source.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>{source.last_scraped ? formatDate(new Date(source.last_scraped)) : 'Never'}</td>
                    <td>
                      <div className="actions">
                        <button className="btn btn-sm btn-outline">Edit</button>
                        <button className="btn btn-sm btn-outline">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <p>No grant sources have been added yet.</p>
              <p>Add your first source to start discovering grant opportunities.</p>
            </div>
          )}
        </div>
      </div>
      
      <div className="card mt-4">
        <div className="card-header">
          <h2>Scraping History</h2>
          <button className="btn btn-primary" onClick={runScraper} disabled={isRunning}>
            {isRunning ? 'Running...' : 'Run Scraper Now'}
          </button>
        </div>
        <div className="card-body">
          {isRunning && (
            <div className="text-center mb-4">
              <div className="spinner-border text-primary" role="status">
                <span className="sr-only">Running...</span>
              </div>
              <p className="mt-2">Please wait while the scraper runs. This may take a few minutes.</p>
            </div>
          )}
          
          {history.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Sources Scraped</th>
                  <th>Grants Found</th>
                  <th>Grants Added</th>
                </tr>
              </thead>
              <tbody>
                {history.map(record => (
                  <tr key={record.id}>
                    <td>{formatDate(new Date(record.start_time))}</td>
                    <td>
                      <span className={`badge ${record.status === 'completed' ? 'badge-success' : record.status === 'failed' ? 'badge-danger' : 'badge-info'}`}>
                        {record.status}
                      </span>
                    </td>
                    <td>{record.sources_scraped}</td>
                    <td>{record.grants_found}</td>
                    <td>{record.grants_added}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              <p>No scraping jobs have been run yet.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper function to format currency
function formatCurrency(amount) {
  if (amount === null || amount === undefined) return 'N/A';
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
}

// Helper function to format dates
function formatDate(date) {
  if (!date) return 'N/A';
  if (!(date instanceof Date) || isNaN(date)) return 'Invalid date';
  
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return date.toLocaleDateString(undefined, options);
}

// Render the React application
ReactDOM.render(
  <App />,
  document.getElementById('root')
);
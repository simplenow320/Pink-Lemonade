// React components for GrantFlow application

// Utility functions for formatting
function formatCurrency(amount) {
  if (!amount || amount === 0) return '$0';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
}

function formatDate(date) {
  if (!date) return 'No date';
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

function getMatchScoreClass(score) {
  if (!score) return 'badge-secondary';
  if (score >= 80) return 'badge-success';
  if (score >= 60) return 'badge-warning';
  return 'badge-danger';
}

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
      
      // Fetch both dashboard data and grants data for the dashboard
      Promise.all([
        fetch('/api/grants/dashboard').then(response => response.json()),
        fetch('/api/grants').then(response => response.json())
      ])
        .then(([dashboardData, grantsData]) => {
          setDashboardData(dashboardData);
          setGrants(grantsData);
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

  // Fetch funders data when viewing funders page
  const [funders, setFunders] = React.useState([]);
  
  React.useEffect(() => {
    if (page === 'funders') {
      setLoading(true);
      fetch('/api/scraper/sources')
        .then(response => response.json())
        .then(data => {
          setFunders(data);
          setLoading(false);
        })
        .catch(error => {
          console.error('Error fetching funders:', error);
          setLoading(false);
        });
    }
  }, [page]);

  // Render current page based on state
  const renderPage = () => {
    if (loading) {
      return <LoadingIndicator />;
    }

    switch(page) {
      case 'dashboard':
        return <Dashboard data={dashboardData} grants={grants} hasApiKey={hasApiKey} onNavigate={navigateTo} />;
      case 'grants':
        return <GrantsList grants={grants} hasApiKey={hasApiKey} />;
      case 'organization':
        return <OrganizationProfile organization={organization} />;
      case 'funders':
        return <FundersManagement funders={funders} setFunders={setFunders} />;
      case 'scraper':
        // Redirect to the standalone scraper page
        window.location.href = '/scraper';
        return <LoadingIndicator />;
      default:
        return <Dashboard data={dashboardData} grants={grants} hasApiKey={hasApiKey} onNavigate={navigateTo} />;
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
  
  // Add event listener to close menu when clicking outside
  React.useEffect(() => {
    const closeMenu = (e) => {
      // Check if menu is open and click is outside the mobile-nav
      if (isMenuOpen && !e.target.closest('.mobile-nav') && !e.target.closest('.mobile-menu-button')) {
        setIsMenuOpen(false);
      }
    };
    
    // Add event listener when menu is open
    if (isMenuOpen) {
      document.addEventListener('click', closeMenu);
    }
    
    // Cleanup event listener on component unmount or menu close
    return () => {
      document.removeEventListener('click', closeMenu);
    };
  }, [isMenuOpen]);
  
  // Prevent body scrolling when mobile menu is open
  React.useEffect(() => {
    if (isMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMenuOpen]);

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
              <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('dashboard'); }}>
                <span className="icon">📊</span>
                <span>Dashboard</span>
              </a>
            </li>
            <li className={currentPage === 'grants' ? 'active' : ''}>
              <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('grants'); }}>
                <span className="icon">📝</span>
                <span>Grants</span>
              </a>
            </li>
            <li className={currentPage === 'organization' ? 'active' : ''}>
              <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('organization'); }}>
                <span className="icon">🏢</span>
                <span>Organization</span>
              </a>
            </li>
            <li className={currentPage === 'funders' ? 'active' : ''}>
              <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('funders'); }}>
                <span className="icon">💰</span>
                <span>Funders</span>
              </a>
            </li>
            <li className={currentPage === 'scraper' ? 'active' : ''}>
              <a href="/scraper" target="_blank" rel="noopener noreferrer">
                <span className="icon">🔍</span>
                <span>Grant Scraper</span>
              </a>
            </li>
          </ul>
        </nav>
        
        {/* Mobile menu button with ARIA attributes for accessibility */}
        <button 
          className="mobile-menu-button" 
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-expanded={isMenuOpen}
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
        >
          <span className="icon">{isMenuOpen ? '✕' : '☰'}</span>
        </button>
      </div>
      
      {/* Mobile navigation - Using 'active' class for animation */}
      <nav className={`mobile-nav ${isMenuOpen ? 'active' : ''}`}>
        <ul>
          <li className={currentPage === 'dashboard' ? 'active' : ''}>
            <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('dashboard'); setIsMenuOpen(false); }}>
              <span className="icon">📊</span>
              <span>Dashboard</span>
            </a>
          </li>
          <li className={currentPage === 'grants' ? 'active' : ''}>
            <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('grants'); setIsMenuOpen(false); }}>
              <span className="icon">📝</span>
              <span>Grants</span>
            </a>
          </li>
          <li className={currentPage === 'organization' ? 'active' : ''}>
            <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('organization'); setIsMenuOpen(false); }}>
              <span className="icon">🏢</span>
              <span>Organization</span>
            </a>
          </li>
          <li className={currentPage === 'funders' ? 'active' : ''}>
            <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('funders'); setIsMenuOpen(false); }}>
              <span className="icon">💰</span>
              <span>Funders</span>
            </a>
          </li>
          <li className={currentPage === 'scraper' ? 'active' : ''}>
            <a href="/scraper" target="_blank" rel="noopener noreferrer">
              <span className="icon">🔍</span>
              <span>Grant Scraper</span>
            </a>
          </li>
          {/* Adding organization name in mobile menu */}
          {organization && (
            <li className="organization-info">
              <div className="organization-name">
                {organization.name || "Your Organization"}
              </div>
            </li>
          )}
        </ul>
      </nav>
      
      {/* Overlay when mobile menu is open */}
      {isMenuOpen && (
        <div 
          className="mobile-menu-overlay" 
          onClick={() => setIsMenuOpen(false)}
          aria-hidden="true"
        />
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
      <div className="container">
        <h1>{getPageTitle()}</h1>
        <div className="header-actions">
          {page === 'grants' && (
            <button className="btn btn-primary">Add Grant</button>
          )}
          {page === 'organization' && (
            <button className="btn btn-primary">Edit Profile</button>
          )}
        </div>
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
function Dashboard({ data, grants, hasApiKey, onNavigate }) {
  const [isDiscovering, setIsDiscovering] = React.useState(false);
  const [discoveryProgress, setDiscoveryProgress] = React.useState({
    sites: 0,
    queries: 0,
    successful: 0,
    grants: 0
  });

  const handleDiscoverGrants = async () => {
    if (!hasApiKey) {
      alert('OpenAI API key is required for grant discovery. Please configure it in your environment.');
      return;
    }

    setIsDiscovering(true);
    setDiscoveryProgress({ sites: 0, queries: 0, successful: 0, grants: 0 });

    try {
      // Start the scraping job
      const response = await fetch('/api/scraper/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ include_web_search: true })
      });

      if (response.ok) {
        // Poll for progress updates
        const pollProgress = async () => {
          try {
            const historyResponse = await fetch('/api/scraper/history?limit=1');
            const historyData = await historyResponse.json();
            
            if (historyData && historyData.length > 0) {
              const latestJob = historyData[0];
              
              if (latestJob.status === 'in_progress') {
                setDiscoveryProgress({
                  sites: latestJob.sites_searched || latestJob.search_report?.sites_searched || 0,
                  queries: latestJob.queries_attempted || latestJob.search_report?.queries_attempted || 0,
                  successful: latestJob.successful_queries || latestJob.search_report?.successful_queries || 0,
                  grants: latestJob.grants_found || 0
                });
                
                // Continue polling
                setTimeout(pollProgress, 2000);
              } else {
                // Discovery completed
                setIsDiscovering(false);
                // Refresh page data
                window.location.reload();
              }
            }
          } catch (error) {
            console.error('Error polling progress:', error);
          }
        };

        // Start polling after a short delay
        setTimeout(pollProgress, 1000);
      } else {
        throw new Error('Failed to start grant discovery');
      }
    } catch (error) {
      console.error('Error starting grant discovery:', error);
      setIsDiscovering(false);
      alert('Failed to start grant discovery. Please try again.');
    }
  };

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
    <div className="dashboard-container">
      {!hasApiKey && (
        <div className="container">
          <div className="alert alert-warning">
            <strong>OpenAI API Key Required:</strong> To enable AI-powered features like grant matching and narrative generation, please add your OpenAI API key in the settings.
          </div>
        </div>
      )}
      
      <div className="welcome-hero">
        <div className="container">
          <div className="hero-content-centered">
            <h1 className="hero-title">Discover & Manage<br />Grants Efficiently</h1>
            <p className="hero-subtitle">
              GrantFlow helps you find the perfect funding opportunities for your nonprofit organization with AI-powered matching and automated discovery.
            </p>
            <div className="hero-actions">
              <button 
                onClick={handleDiscoverGrants} 
                disabled={isDiscovering}
                className="btn btn-primary"
              >
                {isDiscovering ? 'Discovering Grants...' : 'Discover Grants'}
              </button>
              <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('grants'); }} className="btn btn-outline">View All Grants</a>
            </div>
            
            {isDiscovering && (
              <div className="discovery-progress">
                <div className="progress-info">
                  <p>🔍 Searching for grants that match your organization...</p>
                  <div className="progress-stats">
                    <span><strong>{discoveryProgress.sites}</strong> sites searched</span>
                    <span><strong>{discoveryProgress.successful}/{discoveryProgress.queries}</strong> successful queries</span>
                    <span><strong>{discoveryProgress.grants}</strong> grants found</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="container">
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
                <div className="table-responsive">
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
                </div>
              ) : (
                <p>No upcoming deadlines</p>
              )}
            </div>
          </div>
        </div>
        
        <div className="dashboard-section">
          <h2>Recent Grants</h2>
          <div className="card">
            <div className="card-body">
              {grants && grants.length > 0 ? (
                <div className="table-responsive">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Grant</th>
                        <th>Funder</th>
                        <th>Amount</th>
                        <th>Match Score</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {grants.slice(0, 5).map(grant => (
                        <tr key={grant.id}>
                          <td>
                            <div className="grant-title">{grant.title}</div>
                            <div className="grant-description-small">{grant.description?.substring(0, 100)}...</div>
                          </td>
                          <td>{grant.funder}</td>
                          <td>{grant.amount ? formatCurrency(grant.amount) : 'Not specified'}</td>
                          <td>
                            <span className={`badge ${getMatchScoreClass(grant.match_score)}`}>
                              {grant.match_score ? `${grant.match_score}/100` : 'N/A'}
                            </span>
                          </td>
                          <td>
                            <span className={`badge status-${grant.status?.toLowerCase().replace(/\s+/g, '-')}`}>
                              {grant.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="no-grants-message">
                  <p>No grants found. Click "Discover Grants" to find funding opportunities.</p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="dashboard-section">
          <h2>Grants by Status</h2>
          <div className="card">
            <div className="card-body">
              <div className="grants-by-status">
                {data.status_counts && Object.entries(data.status_counts).map(([status, count]) => (
                  <div 
                    key={status} 
                    className={`status-item status-${status.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <div className="status-label">{status}</div>
                    <div className="status-value">{count}</div>
                  </div>
                ))}
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
                <div className="table-responsive">
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
                </div>
              ) : (
                <p>No grants have been discovered in the last 7 days. Use the Grant Scraper to find more opportunities.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Grants list component
function GrantsList({ grants, hasApiKey }) {
  const [formData, setFormData] = React.useState({
    title: '',
    description: '',
    due_date: '',
    amount: '',
    eligibility: '',
    status: 'Not Started',
    funder: 'Unknown'
  });
  
  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };
  
  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.title) {
      alert('Please enter a grant title');
      return;
    }
    
    // Show loading indicator
    document.getElementById('loading-overlay').style.display = 'flex';
    
    // Send form data to API
    fetch('/api/grants', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      // Hide loading indicator
      document.getElementById('loading-overlay').style.display = 'none';
      
      // Show success message
      alert('Grant added successfully!');
      
      // Clear form
      setFormData({
        title: '',
        description: '',
        due_date: '',
        amount: '',
        eligibility: '',
        status: 'Not Started',
        funder: 'Unknown'
      });
      
      // Refresh grants list
      window.location.reload();
    })
    .catch(error => {
      // Hide loading indicator
      document.getElementById('loading-overlay').style.display = 'none';
      
      // Show error message
      console.error('Error adding grant:', error);
      alert('Failed to add grant. Please try again.');
    });
  };
  
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

      {/* Add Grant Form */}
      <div className="card mt-4">
        <div className="card-header">
          <h3>Add New Grant</h3>
        </div>
        <div className="card-body">
          <form id="grantForm" onSubmit={handleSubmit}>
            <div className="form-group mb-3">
              <label htmlFor="title">Title</label>
              <input 
                type="text" 
                className="form-control" 
                id="title" 
                name="title" 
                placeholder="Grant Title" 
                required 
                value={formData.title}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group mb-3">
              <label htmlFor="summary">Summary</label>
              <textarea 
                className="form-control" 
                id="summary" 
                name="description" 
                rows="3" 
                placeholder="Grant Summary"
                value={formData.description}
                onChange={handleInputChange}
              ></textarea>
            </div>

            <div className="row">
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label htmlFor="dueDate">Due Date</label>
                  <input 
                    type="date" 
                    className="form-control" 
                    id="dueDate" 
                    name="due_date"
                    value={formData.due_date}
                    onChange={handleInputChange}
                  />
                </div>
              </div>
              <div className="col-md-6">
                <div className="form-group mb-3">
                  <label htmlFor="amount">Amount</label>
                  <input 
                    type="number" 
                    className="form-control" 
                    id="amount" 
                    name="amount" 
                    placeholder="Grant Amount"
                    step="0.01" 
                    min="0"
                    value={formData.amount}
                    onChange={handleInputChange}
                  />
                </div>
              </div>
            </div>

            <div className="form-group mb-3">
              <label htmlFor="eligibility">Eligibility Criteria</label>
              <textarea 
                className="form-control" 
                id="eligibility" 
                name="eligibility" 
                rows="3" 
                placeholder="Eligibility Requirements"
                value={formData.eligibility}
                onChange={handleInputChange}
              ></textarea>
            </div>

            <div className="form-group mb-3">
              <label htmlFor="status">Status</label>
              <select 
                className="form-control" 
                id="status" 
                name="status"
                value={formData.status}
                onChange={handleInputChange}
              >
                <option value="Not Started">Not Started</option>
                <option value="In Progress">In Progress</option>
                <option value="Submitted">Submitted</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>

            <button type="submit" className="btn btn-primary">Save Grant</button>
          </form>
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

// Funders Management Component
function FundersManagement({ funders, setFunders }) {
  const [showAddForm, setShowAddForm] = React.useState(false);
  const [editingFunder, setEditingFunder] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [formData, setFormData] = React.useState({
    name: '',
    url: '',
    location: '',
    phone: '',
    contact_email: '',
    contact_name: '',
    match_score: 3,
    best_fit_initiatives: [],
    grant_programs: [],
    is_active: true
  });
  const [initiatives, setInitiatives] = React.useState([
    'Urban Church Planting',
    'Mental Health and the Church',
    'Pastors Thriving Together',
    'AI, The Church, and Urban Communities'
  ]);
  const [message, setMessage] = React.useState({ text: '', type: '' });

  // Reset form when add/edit mode changes
  React.useEffect(() => {
    if (editingFunder) {
      setFormData({
        name: editingFunder.name || '',
        url: editingFunder.url || '',
        location: editingFunder.location || '',
        phone: editingFunder.phone || '',
        contact_email: editingFunder.contact_email || '',
        contact_name: editingFunder.contact_name || '',
        match_score: editingFunder.match_score || 3,
        best_fit_initiatives: editingFunder.best_fit_initiatives || [],
        grant_programs: editingFunder.grant_programs || [],
        is_active: editingFunder.is_active !== false
      });
    } else {
      resetForm();
    }
  }, [editingFunder, showAddForm]);

  // Reset form to defaults
  const resetForm = () => {
    setFormData({
      name: '',
      url: '',
      location: '',
      phone: '',
      contact_email: '',
      contact_name: '',
      match_score: 3,
      best_fit_initiatives: [],
      grant_programs: [],
      is_active: true
    });
  };

  // Handle form input changes
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // Handle multi-select changes for initiatives
  const handleInitiativeChange = (initiative) => {
    if (formData.best_fit_initiatives.includes(initiative)) {
      setFormData({
        ...formData,
        best_fit_initiatives: formData.best_fit_initiatives.filter(i => i !== initiative)
      });
    } else {
      setFormData({
        ...formData,
        best_fit_initiatives: [...formData.best_fit_initiatives, initiative]
      });
    }
  };

  // Handle grant program input
  const handleAddProgram = () => {
    const programInput = document.getElementById('program-input');
    if (programInput && programInput.value.trim()) {
      setFormData({
        ...formData,
        grant_programs: [...formData.grant_programs, programInput.value.trim()]
      });
      programInput.value = '';
    }
  };

  const handleRemoveProgram = (program) => {
    setFormData({
      ...formData,
      grant_programs: formData.grant_programs.filter(p => p !== program)
    });
  };

  // Submit form to add or update funder
  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Validate form
    if (!formData.name || !formData.url) {
      setMessage({ text: 'Name and URL are required', type: 'error' });
      setLoading(false);
      return;
    }

    // Determine if adding or updating
    const isUpdating = !!editingFunder;
    const url = isUpdating 
      ? `/api/scraper/sources/${editingFunder.id}` 
      : '/api/scraper/sources';
    const method = isUpdating ? 'PUT' : 'POST';

    fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to save funder');
        }
        return response.json();
      })
      .then(data => {
        // Update local state
        if (isUpdating) {
          setFunders(funders.map(f => f.id === editingFunder.id ? data : f));
        } else {
          setFunders([...funders, data]);
        }
        
        // Show success message
        setMessage({ 
          text: `Funder ${isUpdating ? 'updated' : 'added'} successfully`, 
          type: 'success' 
        });
        
        // Reset form
        setShowAddForm(false);
        setEditingFunder(null);
        resetForm();
      })
      .catch(error => {
        console.error('Error saving funder:', error);
        setMessage({ text: error.message, type: 'error' });
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Delete a funder
  const handleDelete = (funder) => {
    if (!window.confirm(`Are you sure you want to delete ${funder.name}?`)) {
      return;
    }

    setLoading(true);
    fetch(`/api/scraper/sources/${funder.id}`, {
      method: 'DELETE'
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to delete funder');
        }
        return response.json();
      })
      .then(() => {
        setFunders(funders.filter(f => f.id !== funder.id));
        setMessage({ text: 'Funder deleted successfully', type: 'success' });
      })
      .catch(error => {
        console.error('Error deleting funder:', error);
        setMessage({ text: error.message, type: 'error' });
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Clear message after 5 seconds
  React.useEffect(() => {
    if (message.text) {
      const timer = setTimeout(() => {
        setMessage({ text: '', type: '' });
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  return (
    <div className="page-container funders-page">
      <h1>Manage Funders</h1>
      
      {/* Message display */}
      {message.text && (
        <div className={`alert ${message.type === 'error' ? 'alert-danger' : 'alert-success'}`}>
          {message.text}
        </div>
      )}
      
      {/* Add/Edit Form Toggle Button */}
      {!showAddForm && !editingFunder && (
        <button 
          className="btn btn-primary mb-4" 
          onClick={() => setShowAddForm(true)}
        >
          Add New Funder
        </button>
      )}
      
      {/* Add/Edit Form */}
      {(showAddForm || editingFunder) && (
        <div className="card mb-4">
          <div className="card-header">
            <h3>{editingFunder ? 'Edit Funder' : 'Add New Funder'}</h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group col-md-6">
                  <label htmlFor="name">Funder Name*</label>
                  <input
                    type="text"
                    className="form-control"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group col-md-6">
                  <label htmlFor="url">Website URL*</label>
                  <input
                    type="url"
                    className="form-control"
                    id="url"
                    name="url"
                    value={formData.url}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group col-md-6">
                  <label htmlFor="location">Location</label>
                  <input
                    type="text"
                    className="form-control"
                    id="location"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-group col-md-6">
                  <label htmlFor="phone">Phone Number</label>
                  <input
                    type="tel"
                    className="form-control"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group col-md-6">
                  <label htmlFor="contact_name">Contact Person</label>
                  <input
                    type="text"
                    className="form-control"
                    id="contact_name"
                    name="contact_name"
                    value={formData.contact_name}
                    onChange={handleChange}
                  />
                </div>
                <div className="form-group col-md-6">
                  <label htmlFor="contact_email">Contact Email</label>
                  <input
                    type="email"
                    className="form-control"
                    id="contact_email"
                    name="contact_email"
                    value={formData.contact_email}
                    onChange={handleChange}
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="match_score">Match Score (1-5)</label>
                <input
                  type="range"
                  className="form-control-range"
                  id="match_score"
                  name="match_score"
                  min="1"
                  max="5"
                  value={formData.match_score}
                  onChange={handleChange}
                />
                <div className="d-flex justify-content-between">
                  <span>Low Match</span>
                  <span>Current: {formData.match_score}</span>
                  <span>High Match</span>
                </div>
              </div>
              
              <div className="form-group">
                <label>Best Fit Initiatives</label>
                <div className="initiative-checkboxes">
                  {initiatives.map(initiative => (
                    <div className="form-check" key={initiative}>
                      <input
                        type="checkbox"
                        className="form-check-input"
                        id={`initiative-${initiative}`}
                        checked={formData.best_fit_initiatives.includes(initiative)}
                        onChange={() => handleInitiativeChange(initiative)}
                      />
                      <label className="form-check-label" htmlFor={`initiative-${initiative}`}>
                        {initiative}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="form-group">
                <label>Grant Programs</label>
                <div className="input-group mb-2">
                  <input
                    type="text"
                    className="form-control"
                    id="program-input"
                    placeholder="Enter grant program name"
                  />
                  <div className="input-group-append">
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={handleAddProgram}
                    >
                      Add
                    </button>
                  </div>
                </div>
                
                <div className="grant-programs-list">
                  {formData.grant_programs.map(program => (
                    <div key={program} className="badge badge-secondary program-badge">
                      {program}
                      <button
                        type="button"
                        className="close ml-1"
                        onClick={() => handleRemoveProgram(program)}
                      >
                        &times;
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  className="form-check-input"
                  id="is_active"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                />
                <label className="form-check-label" htmlFor="is_active">Active</label>
              </div>
              
              <div className="form-actions">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : (editingFunder ? 'Update Funder' : 'Add Funder')}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary ml-2"
                  onClick={() => {
                    setShowAddForm(false);
                    setEditingFunder(null);
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Funders List */}
      <div className="card">
        <div className="card-header">
          <h3>All Funders ({funders.length})</h3>
        </div>
        <div className="card-body">
          {funders.length > 0 ? (
            <div className="table-responsive">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Website</th>
                    <th>Location</th>
                    <th>Contact</th>
                    <th>Match Score</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {funders.map(funder => (
                    <tr key={funder.id} className={funder.is_active ? '' : 'text-muted'}>
                      <td>{funder.name}</td>
                      <td>
                        <a href={funder.url} target="_blank" rel="noopener noreferrer">
                          {new URL(funder.url).hostname}
                        </a>
                      </td>
                      <td>{funder.location || 'N/A'}</td>
                      <td>
                        {funder.contact_name ? (
                          <div>
                            <div>{funder.contact_name}</div>
                            {funder.contact_email && (
                              <a href={`mailto:${funder.contact_email}`} className="small">
                                {funder.contact_email}
                              </a>
                            )}
                          </div>
                        ) : (
                          'N/A'
                        )}
                      </td>
                      <td>
                        <div className="star-rating">
                          {[1, 2, 3, 4, 5].map(star => (
                            <span key={star} className={star <= funder.match_score ? 'star filled' : 'star'}>
                              ★
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${funder.is_active ? 'badge-success' : 'badge-secondary'}`}>
                          {funder.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <div className="btn-group">
                          <button
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => setEditingFunder(funder)}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleDelete(funder)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <p>No funders have been added yet.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Render the React application
console.log('Starting React app initialization...');
console.log('React available:', typeof React !== 'undefined');
console.log('ReactDOM available:', typeof ReactDOM !== 'undefined');
console.log('Root element:', document.getElementById('root'));

try {
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    console.error('Root element not found!');
    throw new Error('Root element not found');
  }
  
  console.log('Rendering React app...');
  ReactDOM.render(
    React.createElement(App),
    rootElement
  );
  console.log('React app rendered successfully!');
} catch (error) {
  console.error('Failed to render React app:', error);
  
  // Fallback HTML content
  const rootElement = document.getElementById('root');
  if (rootElement) {
    rootElement.innerHTML = `
      <div style="padding: 2rem; text-align: center; background: white; margin: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="color: #dc3545; margin-bottom: 1rem;">GrantFlow Loading Error</h1>
        <p style="color: #6c757d; margin-bottom: 1rem;">There was an issue loading the React application.</p>
        <p style="color: #6c757d; font-size: 0.9rem;">Error: ${error.message}</p>
        <button onclick="window.location.reload()" style="background: #007bff; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; margin-top: 1rem;">Reload Page</button>
      </div>
    `;
  }
}
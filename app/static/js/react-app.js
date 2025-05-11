// React components for GrantFlow application

// Main application component
function App() {
  const [currentPage, setCurrentPage] = React.useState('dashboard');
  const [apiKey, setApiKey] = React.useState(null);
  const [apiKeyChecked, setApiKeyChecked] = React.useState(false);
  const [grants, setGrants] = React.useState([]);
  const [organization, setOrganization] = React.useState(null);
  const [dashboardData, setDashboardData] = React.useState({
    upcoming: [],
    recent: [],
    status: {},
    matchStats: {}
  });
  
  // Check if API key is available
  React.useEffect(() => {
    fetch('/api/ai/status')
      .then(response => response.json())
      .then(data => {
        setApiKey(data.api_key_configured);
        setApiKeyChecked(true);
      })
      .catch(error => {
        console.error('Error checking API status:', error);
        setApiKeyChecked(true);
      });
      
    // Load organization profile
    fetch('/api/organization')
      .then(response => response.json())
      .then(data => {
        setOrganization(data);
      })
      .catch(error => {
        console.error('Error fetching organization:', error);
      });
      
    // Load grants
    fetch('/api/grants')
      .then(response => response.json())
      .then(data => {
        setGrants(data);
      })
      .catch(error => {
        console.error('Error fetching grants:', error);
      });
      
    // Load dashboard data
    fetch('/api/grants/dashboard')
      .then(response => response.json())
      .then(data => {
        console.log('Dashboard data:', data);
        setDashboardData({
          upcoming: data.upcoming_deadlines || [],
          recent: data.recently_discovered || [],
          status: {
            active: data.total_grants || 0,
            potential_funding: data.potential_funding || 0,
            success_rate: Math.round((data.won_funding / (data.potential_funding || 1)) * 100) || 0
          },
          matchStats: data.match_score_distribution || {}
        });
      })
      .catch(error => {
        console.error('Error fetching dashboard data:', error);
      });
  }, []);
  
  // Handle navigation
  const handleNavigate = (page) => {
    setCurrentPage(page);
  };
  
  return (
    <div className="app-container">
      <TopNavbar 
        currentPage={currentPage} 
        onNavigate={handleNavigate} 
        organization={organization}
      />
      
      {currentPage === 'dashboard' && (
        <Dashboard data={dashboardData} hasApiKey={apiKey} onNavigate={handleNavigate} />
      )}
      
      {currentPage === 'grants' && (
        <GrantsList grants={grants} hasApiKey={apiKey} />
      )}
      
      {currentPage === 'organization' && (
        <OrganizationProfile organization={organization} />
      )}
      
      {currentPage === 'scraper' && (
        <ScraperSettings hasApiKey={apiKey} />
      )}
      
      {/* Loading indicator */}
      <div id="loading-overlay" style={{display: 'none'}}>
        <div className="spinner"></div>
      </div>
    </div>
  );
}

// Top navigation bar component - Modern, mobile-first design
function TopNavbar({ currentPage, onNavigate, organization }) {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [scrolled, setScrolled] = React.useState(false);
  
  // Handle scroll effect for glass-like navbar on scroll
  React.useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 10) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  // Navigation items with icons
  const navItems = [
    { name: 'Dashboard', id: 'dashboard', icon: 'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zm-10 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z' },
    { name: 'Grants', id: 'grants', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
    { name: 'Organization', id: 'organization', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
    { name: 'Discover', id: 'scraper', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' }
  ];
  
  return (
    <header className={`top-navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-container">
        {/* Logo */}
        <div className="navbar-logo">
          <h1>
            <span className="text-primary">Grant</span>
            <span className="text-primary-dark">Flow</span>
          </h1>
        </div>
        
        {/* Desktop navigation */}
        <nav className="desktop-nav">
          <ul>
            {navItems.map((item) => (
              <li key={item.id} className={currentPage === item.id ? 'active' : ''}>
                <a href="#" onClick={(e) => { 
                  e.preventDefault(); 
                  onNavigate(item.id); 
                }}>
                  <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d={item.icon}></path>
                  </svg>
                  {item.name}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        
        {/* Organization name on desktop */}
        <div className="user-info desktop-only">
          {organization && organization.name ? organization.name : 'My Organization'}
        </div>
        
        {/* Mobile menu button */}
        <button 
          className="mobile-menu-button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-expanded={mobileMenuOpen}
          aria-label="Toggle navigation menu"
        >
          <div className={`hamburger ${mobileMenuOpen ? 'active' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </button>
      </div>
      
      {/* Mobile menu */}
      <div className={`mobile-nav ${mobileMenuOpen ? 'active' : ''}`}>
        <ul className="mobile-nav-links">
          <li>
            <div className="mobile-user-info">
              {/* Adding organization name in mobile menu */}
              {organization && organization.name ? organization.name : 'My Organization'}
            </div>
          </li>
          {navItems.map((item) => (
            <li key={item.id} className={currentPage === item.id ? 'active' : ''}>
              <a href="#" onClick={(e) => { 
                e.preventDefault(); 
                onNavigate(item.id); 
                setMobileMenuOpen(false);
              }}>
                <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d={item.icon}></path>
                </svg>
                {item.name}
              </a>
            </li>
          ))}
        </ul>
      </div>
      
      {/* Overlay when mobile menu is open */}
      <div 
        className={`mobile-nav-overlay ${mobileMenuOpen ? 'active' : ''}`}
        onClick={() => setMobileMenuOpen(false)}
      ></div>
    </header>
  );
}

// Header component
function Header({ page, organization }) {
  return (
    <div className="container">
      <div className="header">
        <h1>{page}</h1>
        {organization && organization.name && (
          <div className="organization-name">
            {organization.name}
          </div>
        )}
      </div>
    </div>
  );
}

// Loading indicator component
function LoadingIndicator() {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
    </div>
  );
}

// Dashboard component
function Dashboard({ data, hasApiKey, onNavigate }) {
  if (!data) {
    return (
      <div className="container">
        <div className="card">
          <div className="card-body">
            <LoadingIndicator />
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="dashboard-container">
      <Header page="Dashboard" />
      
      <div className="dashboard-summary">
        <div className="summary-card">
          <div className="summary-icon">📝</div>
          <div className="summary-content">
            <h3>Active Grants</h3>
            <div className="summary-value">{data.status ? data.status.active || 0 : 0}</div>
          </div>
        </div>
        
        <div className="summary-card">
          <div className="summary-icon">💰</div>
          <div className="summary-content">
            <h3>Potential Funding</h3>
            <div className="summary-value">${data.status ? (data.status.potential_funding || 0).toLocaleString() : 0}</div>
          </div>
        </div>
        
        <div className="summary-card">
          <div className="summary-icon">🏆</div>
          <div className="summary-content">
            <h3>Success Rate</h3>
            <div className="summary-value">{data.status ? data.status.success_rate || 0 : 0}%</div>
          </div>
        </div>
        
        <div className="summary-card">
          <div className="summary-icon">⏰</div>
          <div className="summary-content">
            <h3>Upcoming Deadlines</h3>
            <div className="summary-value">{data.upcoming ? data.upcoming.length : 0}</div>
          </div>
        </div>
      </div>
      
      <div className="dashboard-sections">
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Upcoming Deadlines</h2>
          </div>
          
          <div className="card">
            <div className="card-body">
              {data.upcoming && data.upcoming.length > 0 ? (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Grant</th>
                      <th>Due Date</th>
                      <th>Status</th>
                      <th>Match</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.upcoming.map(grant => (
                      <tr key={grant.id}>
                        <td>{grant.title}</td>
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
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">
                  <p>No upcoming deadlines.</p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recently Added</h2>
          </div>
          
          <div className="card">
            <div className="card-body">
              {data.recent && data.recent.length > 0 ? (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Grant</th>
                      <th>Funder</th>
                      <th>Added</th>
                      <th>Match</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent.map(grant => (
                      <tr key={grant.id}>
                        <td>{grant.title}</td>
                        <td>{grant.funder}</td>
                        <td>{formatDate(new Date(grant.created_at))}</td>
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
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">
                  <p>No recently added grants.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <div className="dashboard-actions">
        <button 
          className="btn btn-primary" 
          onClick={() => onNavigate('grants')}
        >
          View All Grants
        </button>
        
        <button 
          className="btn btn-secondary" 
          onClick={() => onNavigate('scraper')}
        >
          Discover Grants
        </button>
      </div>
      
      {!hasApiKey && (
        <div className="api-key-alert">
          <div className="alert alert-warning">
            <strong>OpenAI API Key Required</strong>
            <p>To use AI-powered features like grant matching and narrative generation, please add your OpenAI API key in the settings.</p>
          </div>
        </div>
      )}
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
      
      // Reload the page
      window.location.reload();
    })
    .catch(error => {
      console.error('Error adding grant:', error);
      document.getElementById('loading-overlay').style.display = 'none';
      alert('Error adding grant. Please try again.');
    });
  };
  
  return (
    <div>
      <Header page="Grants" />
      
      {!hasApiKey && (
        <div className="container mb-4">
          <div className="alert alert-warning">
            <strong>OpenAI API Key Required</strong>
            <p>To use AI-powered features like grant matching and narrative generation, please add your OpenAI API key in the settings.</p>
          </div>
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

            <div className="form-row">
              <div className="form-group mb-3">
                <label htmlFor="funder">Funder</label>
                <input 
                  type="text" 
                  className="form-control" 
                  id="funder" 
                  name="funder" 
                  placeholder="Funding Organization"
                  value={formData.funder}
                  onChange={handleInputChange}
                />
              </div>

              <div className="form-group mb-3">
                <label htmlFor="amount">Amount</label>
                <input 
                  type="number" 
                  className="form-control" 
                  id="amount" 
                  name="amount" 
                  placeholder="Grant Amount"
                  value={formData.amount}
                  onChange={handleInputChange}
                />
              </div>

              <div className="form-group mb-3">
                <label htmlFor="due_date">Due Date</label>
                <input 
                  type="date" 
                  className="form-control" 
                  id="due_date" 
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            <div className="form-group mb-3">
              <label htmlFor="eligibility">Eligibility</label>
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
            <LoadingIndicator />
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div>
      <Header page="Organization Profile" />
      
      <div className="profile-container">
        <div className="profile-section">
          <div className="profile-header">
            <h2>Organization Details</h2>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Organization Name</div>
            <div className="profile-value">{organization.name || 'Not provided'}</div>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Mission Statement</div>
            <div className="profile-value">{organization.mission || 'No mission statement provided.'}</div>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Website</div>
            <div className="profile-value">
              {organization.website ? (
                <a href={organization.website} target="_blank" rel="noopener noreferrer">{organization.website}</a>
              ) : (
                'No website provided.'
              )}
            </div>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Year Founded</div>
            <div className="profile-value">{organization.year_founded || 'Not provided'}</div>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Tax ID / EIN</div>
            <div className="profile-value">{organization.tax_id || 'Not provided'}</div>
          </div>
        </div>
        
        <div className="profile-section">
          <div className="profile-header">
            <h2>Contact Information</h2>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Contact Name</div>
            <div className="profile-value">{organization.contact_name || 'Not provided'}</div>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Email</div>
            <div className="profile-value">{organization.contact_email || 'Not provided'}</div>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Phone</div>
            <div className="profile-value">{organization.contact_phone || 'Not provided'}</div>
          </div>
          
          <div className="profile-field">
            <div className="profile-label">Address</div>
            <div className="profile-value">{organization.address || 'Not provided'}</div>
          </div>
        </div>
        
        <div className="profile-section">
          <div className="profile-header">
            <h2>Focus Areas</h2>
          </div>
          
          <div className="profile-field">
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
        setRunStatus({ 
          status: 'success', 
          message: `Scraping completed! Found ${data.grants_added} new grants.` 
        });
        
        // Refresh data
        fetchData();
        
        // Reset running state after a delay
        setTimeout(() => {
          setIsRunning(false);
        }, 2000);
      })
      .catch(error => {
        console.error('Error running scraper:', error);
        setRunStatus({ status: 'error', message: 'Error running scraper. Please try again.' });
        setIsRunning(false);
      });
  };
  
  return (
    <div>
      <Header page="Discover Grants" />
      
      {!hasApiKey && (
        <div className="container mb-4">
          <div className="alert alert-warning">
            <strong>OpenAI API Key Required</strong>
            <p>
              The grant scraper uses OpenAI to extract structured grant information from funding sources.
              Please add your OpenAI API key in the settings to enable this feature.
            </p>
          </div>
        </div>
      )}
      
      <div className="scraper-actions">
        <button 
          className={`btn ${isRunning ? 'btn-secondary' : 'btn-primary'}`}
          onClick={runScraper}
          disabled={isRunning || !hasApiKey}
        >
          {isRunning ? 'Scraping...' : 'Run Scraper Now'}
        </button>
        
        {runStatus && (
          <div className={`scraper-status ${runStatus.status}`}>
            {runStatus.message}
          </div>
        )}
      </div>
      
      <div className="scraper-sections">
        <div className="scraper-section">
          <div className="section-header">
            <h2>Scraper Sources</h2>
            <p>These sources are checked regularly for new grant opportunities.</p>
          </div>
          
          {loading ? (
            <LoadingIndicator />
          ) : (
            <div className="card">
              <div className="card-body">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>URL</th>
                      <th>Last Checked</th>
                      <th>Status</th>
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
                        <td>{source.last_run ? formatDate(new Date(source.last_run)) : 'Never'}</td>
                        <td>
                          <span className={`badge ${source.active ? 'badge-success' : 'badge-danger'}`}>
                            {source.active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
        
        <div className="scraper-section">
          <div className="section-header">
            <h2>Scraping History</h2>
            <p>Recent scraping jobs and results.</p>
          </div>
          
          <div className="card">
            <div className="card-body">
              {history.length > 0 ? (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Sources Checked</th>
                      <th>Grants Found</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map(item => (
                      <tr key={item.id}>
                        <td>{formatDate(new Date(item.run_date))}</td>
                        <td>{item.sources_checked}</td>
                        <td>{item.grants_found}</td>
                        <td>
                          <span className={`badge ${item.status === 'success' ? 'badge-success' : 'badge-danger'}`}>
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">
                  <p>No scraping history available.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Utility functions
function formatCurrency(amount) {
  if (!amount) return '$0';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
}

function formatDate(date) {
  if (!date || isNaN(date)) return 'No date';
  
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return date.toLocaleDateString(undefined, options);
}

// Render the React application
ReactDOM.render(
  <App />,
  document.getElementById('root')
);
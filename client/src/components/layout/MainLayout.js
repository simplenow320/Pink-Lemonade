import React from 'react';
import { Link, useLocation } from 'react-router-dom';

// Modern layout with a clean, sleek design
const MainLayout = ({ children }) => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  
  // Navigation items with modern icons
  const navItems = [
    { name: 'Dashboard', path: '/', icon: DashboardIcon },
    { name: 'Grants', path: '/grants', icon: GrantsIcon },
    { name: 'Organization', path: '/organization', icon: OrganizationIcon },
    { name: 'Scraper', path: '/scraper', icon: ScraperIcon },
    { name: 'Analytics', path: '/analytics', icon: AnalyticsIcon },
    { name: 'Writing', path: '/writing-assistant', icon: WritingIcon }
  ];
  
  // Check if a path is active
  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <header className="bg-white shadow-sm fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/" className="flex-shrink-0 flex items-center">
                <span className="text-xl font-extrabold tracking-tight text-orange-500">
                  <span className="inline-block">Grant</span>
                  <span className="inline-block text-orange-600">Flow</span>
                </span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-4">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ease-in-out ${
                    isActive(item.path)
                      ? 'bg-orange-50 text-orange-600'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-orange-500'
                  }`}
                >
                  <item.icon
                    className={`mr-2 h-5 w-5 ${
                      isActive(item.path) ? 'text-orange-500' : 'text-gray-400'
                    }`}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              ))}
            </nav>

            {/* Mobile menu button */}
            <div className="flex items-center md:hidden">
              <button
                type="button"
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-orange-500 hover:bg-gray-100 focus:outline-none"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                <span className="sr-only">Open main menu</span>
                {!mobileMenuOpen ? (
                  <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                ) : (
                  <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu, show/hide based on menu state */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-b border-gray-100 shadow-lg">
            <div className="pt-2 pb-3 space-y-1 px-4">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center px-3 py-2 rounded-md text-base font-medium ${
                    isActive(item.path)
                      ? 'bg-orange-50 text-orange-600'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-orange-500'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <item.icon
                    className={`mr-3 h-6 w-6 ${
                      isActive(item.path) ? 'text-orange-500' : 'text-gray-400'
                    }`}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="pt-20 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

// Modern, minimalist icon components
const DashboardIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="3" y="3" width="7" height="7" rx="1" fill="currentColor" fillOpacity="0.2" />
    <rect x="3" y="14" width="7" height="7" rx="1" fill="currentColor" fillOpacity="0.2" />
    <rect x="14" y="3" width="7" height="7" rx="1" fill="currentColor" fillOpacity="0.2" />
    <rect x="14" y="14" width="7" height="7" rx="1" fill="currentColor" fillOpacity="0.2" />
    <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" />
    <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" />
    <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" />
  </svg>
);

const GrantsIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M19 5V19C19 20.1046 18.1046 21 17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H17C18.1046 3 19 3.89543 19 5Z" fill="currentColor" fillOpacity="0.2" />
    <path d="M9 9H15M9 13H15M9 17H13M19 5V19C19 20.1046 18.1046 21 17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H17C18.1046 3 19 3.89543 19 5Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const OrganizationIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" fill="currentColor" fillOpacity="0.2" />
    <path d="M18 18C19.6569 18 21 16.6569 21 15C21 13.3431 19.6569 12 18 12C16.3431 12 15 13.3431 15 15C15 16.6569 16.3431 18 18 18Z" fill="currentColor" fillOpacity="0.2" />
    <path d="M6 18C7.65685 18 9 16.6569 9 15C9 13.3431 7.65685 12 6 12C4.34315 12 3 13.3431 3 15C3 16.6569 4.34315 18 6 18Z" fill="currentColor" fillOpacity="0.2" />
    <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M6 12C4.34315 12 3 13.3431 3 15C3 16.6569 4.34315 18 6 18C7.65685 18 9 16.6569 9 15C9 13.3431 7.65685 12 6 12Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M18 12C16.3431 12 15 13.3431 15 15C15 16.6569 16.3431 18 18 18C19.6569 18 21 16.6569 21 15C21 13.3431 19.6569 12 18 12Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M6 18V20H18V18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ScraperIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" fill="currentColor" fillOpacity="0.2" />
    <path d="M10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M21 21L17 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const AnalyticsIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 13V17M16 8V17M12 3V17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M3 21H21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <rect x="7" y="13" width="2" height="4" fill="currentColor" fillOpacity="0.2" />
    <rect x="15" y="8" width="2" height="9" fill="currentColor" fillOpacity="0.2" />
    <rect x="11" y="3" width="2" height="14" fill="currentColor" fillOpacity="0.2" />
  </svg>
);

const WritingIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 19L19 12L22 15L15 22L12 19Z" fill="currentColor" fillOpacity="0.2" />
    <path d="M18 13L10 5L7 8L15 16L18.0001 13.0001Z" fill="currentColor" fillOpacity="0.2" />
    <path d="M12 19L19 12L22 15L15 22L12 19Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M18 13L16.5 11.5M18 13L10 5L7 8L15 16L18 13Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M7.5 8.5L3 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M6 14L2 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export default MainLayout;
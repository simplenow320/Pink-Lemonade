import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

const ModernLayout = ({ children }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrollPosition, setScrollPosition] = useState(0);
  const location = useLocation();

  // Track scroll position for header styling
  useEffect(() => {
    const handleScroll = () => {
      setScrollPosition(window.scrollY);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu when changing routes
  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  // Navigation items with modern icons
  const navItems = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      description: 'Overview of your grants',
      icon: DashboardIcon,
    },
    {
      name: 'Grants',
      path: '/grants',
      description: 'Manage your grant opportunities',
      icon: GrantsIcon,
    },
    {
      name: 'Organization',
      path: '/organization',
      description: 'Your organization profile',
      icon: OrganizationIcon,
    },
    {
      name: 'Scraper',
      path: '/scraper',
      description: 'Find new grant opportunities',
      icon: ScraperIcon,
    },
    {
      name: 'Analytics',
      path: '/analytics',
      description: 'Track your success metrics',
      icon: AnalyticsIcon,
    },
    {
      name: 'Writing',
      path: '/writing-assistant',
      description: 'AI-powered grant writing',
      icon: WritingIcon,
    },
  ];

  // Check if a path is active
  const isActive = (path) => {
    if (path === '/dashboard') {
      return location.pathname === '/dashboard';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Modern Top Navigation - fixed, with glass effect on scroll */}
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrollPosition > 10 ? 'bg-white shadow-md' : 'bg-white/90 backdrop-blur-sm'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex-shrink-0">
              <Link to="/" className="flex items-center">
                <img 
                  src="/attached_assets/Photoroom_20250810_075737_1754827233457.png" 
                  alt="Pink Lemonade" 
                  className="h-8 w-auto"
                />
              </Link>
            </div>

            {/* Desktop Navigation - hidden on mobile */}
            <nav className="hidden md:flex space-x-1">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`relative px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center ${
                    isActive(item.path)
                      ? 'text-orange-600'
                      : 'text-gray-600 hover:text-orange-500 hover:bg-gray-50'
                  }`}
                >
                  {isActive(item.path) && (
                    <motion.div
                      layoutId="navbar-active-pill"
                      className="absolute inset-0 bg-orange-50 rounded-md -z-10"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                  <item.icon
                    className={`mr-1.5 h-5 w-5 ${
                      isActive(item.path)
                        ? 'text-orange-500'
                        : 'text-gray-400 group-hover:text-orange-500'
                    }`}
                  />
                  <span>{item.name}</span>
                </Link>
              ))}
            </nav>

            {/* Help button - desktop only */}
            <div className="hidden md:flex items-center">
              <button
                type="button"
                className="ml-3 inline-flex items-center px-3 py-1.5 border border-transparent text-xs rounded-md font-medium text-orange-600 bg-orange-50 hover:bg-orange-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
              >
                <QuestionIcon className="mr-1.5 h-4 w-4" />
                Help
              </button>
            </div>

            {/* Mobile menu button */}
            <div className="flex items-center md:hidden">
              <button
                type="button"
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-orange-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-orange-500"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
              >
                <span className="sr-only">Open main menu</span>
                {!isMenuOpen ? (
                  <svg
                    className="block h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  </svg>
                ) : (
                  <svg
                    className="block h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu - slide down animation */}
        <AnimatePresence>
          {isMenuOpen && (
            <motion.div
              className="md:hidden bg-white shadow-lg overflow-hidden"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <motion.div
                className="px-3 pt-2 pb-3 space-y-1"
                initial={{ y: -10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ staggerChildren: 0.05, delayChildren: 0.05 }}
              >
                {navItems.map((item) => (
                  <motion.div key={item.name} className="w-full">
                    <Link
                      to={item.path}
                      className={`flex items-center px-3 py-3 rounded-md ${
                        isActive(item.path)
                          ? 'bg-orange-50 text-orange-600'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-orange-500'
                      }`}
                    >
                      <item.icon
                        className={`mr-3 h-6 w-6 ${
                          isActive(item.path) ? 'text-orange-500' : 'text-gray-400'
                        }`}
                      />
                      <div>
                        <span className="font-medium block">{item.name}</span>
                        <span className="text-xs text-gray-500 block mt-0.5">
                          {item.description}
                        </span>
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Main Content with padding for fixed header */}
      <main className="flex-grow pt-16 pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">{children}</div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center py-6">
            <div className="flex items-center">
              <span className="text-gray-500 text-sm">
                &copy; {new Date().getFullYear()} Pink Lemonade. All rights reserved.
              </span>
            </div>
            <div className="mt-4 md:mt-0 flex space-x-6">
              <Link to="/" className="text-gray-500 hover:text-orange-500 text-sm">
                Privacy Policy
              </Link>
              <Link to="/" className="text-gray-500 hover:text-orange-500 text-sm">
                Terms of Service
              </Link>
              <Link to="/" className="text-gray-500 hover:text-orange-500 text-sm">
                Contact Us
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Icon Components
function DashboardIcon(props) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
}

function GrantsIcon(props) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M7 3C5.89543 3 5 3.89543 5 5V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V9L13 3H7Z"
        fill="currentColor"
        fillOpacity="0.2"
      />
      <path
        d="M9 9H15M9 13H15M9 17H13M13 3L19 9M19 9H15C13.8954 9 13 8.10457 13 7V3M5 5C5 3.89543 5.89543 3 7 3H13"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function OrganizationIcon(props) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M17 21V19C17 16.7909 15.2091 15 13 15H7C4.79086 15 3 16.7909 3 19V21"
        fill="currentColor"
        fillOpacity="0.2"
      />
      <path
        d="M10 11C12.2091 11 14 9.20914 14 7C14 4.79086 12.2091 3 10 3C7.79086 3 6 4.79086 6 7C6 9.20914 7.79086 11 10 11Z"
        fill="currentColor"
        fillOpacity="0.2"
      />
      <path
        d="M17 21V19C17 16.7909 15.2091 15 13 15H7C4.79086 15 3 16.7909 3 19V21H17ZM10 11C12.2091 11 14 9.20914 14 7C14 4.79086 12.2091 3 10 3C7.79086 3 6 4.79086 6 7C6 9.20914 7.79086 11 10 11Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M21 10V16M18 13H24"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ScraperIcon(props) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z"
        fill="currentColor"
        fillOpacity="0.2"
      />
      <path
        d="M10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M20.9984 21.0004L15.9984 16.0004"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function AnalyticsIcon(props) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M7 10V17M12 7V17M17 14V17"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <rect x="6" y="10" width="2" height="7" fill="currentColor" fillOpacity="0.2" />
      <rect x="11" y="7" width="2" height="10" fill="currentColor" fillOpacity="0.2" />
      <rect x="16" y="14" width="2" height="3" fill="currentColor" fillOpacity="0.2" />
      <path d="M3 21H21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function WritingIcon(props) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 19L19 12L22 15L15 22L12 19Z" fill="currentColor" fillOpacity="0.2" />
      <path d="M16 5L15 4L11 8L12 9L16 5Z" fill="currentColor" fillOpacity="0.2" />
      <path
        d="M12 19L19 12L22 15L15 22L12 19Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16 5L15 4L11 8L12 9L16 5Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M11 8L9 10L8 13L11 11L11 8Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M15 4L18 7"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function QuestionIcon(props) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M12 17H12.01M12 14V10M12 7H12.01"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default ModernLayout;

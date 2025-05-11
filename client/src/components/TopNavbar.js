import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

const TopNavbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  
  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      const offset = window.scrollY;
      if (offset > 10) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);
  
  const navItems = [
    { name: 'Dashboard', href: '/', icon: 'dashboard' },
    { name: 'Grants', href: '/grants', icon: 'document' },
    { name: 'Organization', href: '/organization', icon: 'organization' },
    { name: 'Scraper', href: '/scraper', icon: 'search' },
    { name: 'Analytics', href: '/analytics', icon: 'chart' },
    { name: 'Writing', href: '/writing-assistant', icon: 'pen' }
  ];
  
  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-in-out
      ${scrolled ? 'bg-white shadow-md' : 'bg-white/95 backdrop-blur-sm shadow-sm'}`}>
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            {/* Logo */}
            <Link to="/" className="flex-shrink-0 flex items-center">
              <span className="text-xl font-extrabold tracking-tight text-orange-500">
                <span className="inline-block transform">Grant</span>
                <span className="inline-block text-orange-600">Flow</span>
              </span>
            </Link>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md mx-1 transition-colors duration-200 ${
                  isActive(item.href)
                    ? 'bg-orange-50 text-orange-600'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-orange-500'
                }`}
              >
                <span className="inline-flex items-center justify-center w-5 h-5 mr-2">
                  {renderIcon(item.icon, isActive(item.href))}
                </span>
                {item.name}
              </Link>
            ))}
          </div>
          
          {/* Mobile menu button */}
          <div className="flex items-center md:hidden">
            <button
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-orange-500 hover:bg-gray-100 focus:outline-none"
              aria-controls="mobile-menu"
              aria-expanded="false"
              onClick={toggleMenu}
            >
              <span className="sr-only">Open main menu</span>
              {!isMenuOpen ? (
                <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              ) : (
                <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-white border-b border-gray-200 shadow-lg" id="mobile-menu">
          <div className="pt-2 pb-3 space-y-1 px-3">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-3 py-3 text-base font-medium rounded-md ${
                  isActive(item.href)
                    ? 'bg-orange-50 text-orange-600'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-orange-500'
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <span className="inline-flex items-center justify-center w-6 h-6 mr-3">
                  {renderIcon(item.icon, isActive(item.href))}
                </span>
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
};

// Modern, sleek SVG icons
const renderIcon = (iconName, isActive) => {
  const color = isActive ? 'text-orange-500' : 'text-gray-500'; 
  
  switch (iconName) {
    case 'dashboard':
      return (
        <svg className={`w-5 h-5 ${color}`} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 5a1 1 0 011-1h5a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5z" fill="currentColor" opacity="0.2" />
          <path d="M13 5a1 1 0 011-1h5a1 1 0 011 1v5a1 1 0 01-1 1h-5a1 1 0 01-1-1V5z" fill="currentColor" opacity="0.2" />
          <path d="M4 13a1 1 0 011-1h5a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1v-5z" fill="currentColor" opacity="0.2" />
          <path d="M13 13a1 1 0 011-1h5a1 1 0 011 1v5a1 1 0 01-1 1h-5a1 1 0 01-1-1v-5z" fill="currentColor" opacity="0.2" />
          <path d="M5 4a1 1 0 00-1 1v5a1 1 0 001 1h5a1 1 0 001-1V5a1 1 0 00-1-1H5zM14 4a1 1 0 00-1 1v5a1 1 0 001 1h5a1 1 0 001-1V5a1 1 0 00-1-1h-5zM5 12a1 1 0 00-1 1v5a1 1 0 001 1h5a1 1 0 001-1v-5a1 1 0 00-1-1H5zM14 12a1 1 0 00-1 1v5a1 1 0 001 1h5a1 1 0 001-1v-5a1 1 0 00-1-1h-5z" 
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'document':
      return (
        <svg className={`w-5 h-5 ${color}`} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M7 3C5.89543 3 5 3.89543 5 5V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V9L13 3H7Z" fill="currentColor" opacity="0.2" />
          <path d="M9 12H15M9 16H15M13 3L19 9M19 9H15C13.8954 9 13 8.10457 13 7V3M5 5C5 3.89543 5.89543 3 7 3H13M5 5V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V9M5 5H3M13 3H15" 
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'organization':
      return (
        <svg className={`w-5 h-5 ${color}`} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 20H22V18C22 16.3431 20.6569 15 19 15C18.0444 15 17.1931 15.4468 16.6438 16.1429" fill="currentColor" opacity="0.2" />
          <path d="M15 14H9C6.79086 14 5 15.7909 5 18V20H19V18C19 15.7909 17.2091 14 15 14Z" fill="currentColor" opacity="0.2" />
          <path d="M12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z" fill="currentColor" opacity="0.2" />
          <path d="M17 20H22V18C22 16.3431 20.6569 15 19 15C18.0444 15 17.1931 15.4468 16.6438 16.1429M15 14H9C6.79086 14 5 15.7909 5 18V20H19V18C19 15.7909 17.2091 14 15 14ZM12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z" 
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'search':
      return (
        <svg className={`w-5 h-5 ${color}`} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" fill="currentColor" opacity="0.2" />
          <path d="M10 17C13.866 17 17 13.866 17 10C17 6.13401 13.866 3 10 3C6.13401 3 3 6.13401 3 10C3 13.866 6.13401 17 10 17Z" 
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M21 21L15 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'chart':
      return (
        <svg className={`w-5 h-5 ${color}`} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 13H7V21H3V13Z" fill="currentColor" opacity="0.2" />
          <path d="M10 8H14V21H10V8Z" fill="currentColor" opacity="0.2" />
          <path d="M17 3H21V21H17V3Z" fill="currentColor" opacity="0.2" />
          <path d="M3 13H7V21H3V13ZM10 8H14V21H10V8ZM17 3H21V21H17V3Z" 
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'pen':
      return (
        <svg className={`w-5 h-5 ${color}`} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15.2322 5.23223L18.7677 8.76777L7.76777 19.7678L4.23223 16.2322L15.2322 5.23223Z" fill="currentColor" opacity="0.2" />
          <path d="M15.2322 5.23223L18.7677 8.76777M15.2322 5.23223L16.7677 3.69669C17.7441 2.72024 19.3479 2.72024 20.3243 3.69669C21.3007 4.67313 21.3007 6.27691 20.3243 7.25336L18.7677 8.76777M15.2322 5.23223L7.76777 12.6967M18.7677 8.76777L11.3033 16.2322M7.76777 12.6967L4.23223 16.2322L7.76777 19.7678L11.3033 16.2322M7.76777 12.6967L11.3033 16.2322" 
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    default:
      return (
        <svg className={`w-5 h-5 ${color}`} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 9V12M12 12V15M12 12H15M12 12H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" 
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
  }
};

export default TopNavbar;
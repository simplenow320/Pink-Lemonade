import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Sidebar = ({ sidebarOpen, setSidebarOpen }) => {
  const location = useLocation();
  
  // Define navigation items
  const navigation = [
    { name: 'Dashboard', href: '/', icon: 'grid' },
    { name: 'Grants', href: '/grants', icon: 'file-text' },
    { name: 'Organization Profile', href: '/organization', icon: 'users' },
    { name: 'Grant Scraper', href: '/scraper', icon: 'search' },
    { name: 'Analytics', href: '/analytics', icon: 'chart-bar' },
    { name: 'Writing Assistant', href: '/writing-assistant', icon: 'pencil' }
  ];
  
  // Check if the current path matches the nav item
  const isCurrentPath = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <>
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 md:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}
      
      {/* Sidebar for mobile */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out md:hidden ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <SidebarContent 
          navigation={navigation} 
          isCurrentPath={isCurrentPath}
          closeSidebar={() => setSidebarOpen(false)}
        />
      </div>
      
      {/* Sidebar for desktop */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64">
          <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto bg-white border-r">
            <SidebarContent 
              navigation={navigation} 
              isCurrentPath={isCurrentPath}
            />
          </div>
        </div>
      </div>
      
      {/* Mobile header with menu button */}
      <div className="md:hidden bg-white w-full shadow-sm fixed top-0 left-0 z-30 px-4 py-2 flex items-center">
        <button
          type="button"
          className="text-gray-600 hover:text-gray-900 focus:outline-none"
          onClick={() => setSidebarOpen(true)}
        >
          <span className="sr-only">Open sidebar</span>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div className="ml-4 flex-1 flex justify-between items-center">
          <div className="flex-shrink-0 flex items-center">
            <span className="text-xl font-bold text-primary">GrantFlow</span>
          </div>
        </div>
      </div>
    </>
  );
};

// Sidebar content component (used for both mobile and desktop)
const SidebarContent = ({ navigation, isCurrentPath, closeSidebar }) => {
  return (
    <div className="flex flex-col flex-grow h-full">
      {/* Logo */}
      <div className="flex items-center px-4 py-5">
        <div className="flex-shrink-0 flex items-center">
          <span className="text-2xl font-bold text-primary">GrantFlow</span>
        </div>
        {/* Close button for mobile */}
        {closeSidebar && (
          <button
            type="button"
            className="ml-auto text-gray-500 hover:text-gray-900 md:hidden"
            onClick={closeSidebar}
          >
            <span className="sr-only">Close sidebar</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      
      {/* Navigation */}
      <div className="mt-5 flex-grow flex flex-col">
        <nav className="flex-1 px-2 space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`
                group flex items-center px-2 py-2 text-sm font-medium rounded-md
                ${isCurrentPath(item.href)
                  ? 'bg-primary-light text-primary'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}
              `}
              onClick={closeSidebar}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="mr-3 flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={getIconPath(item.icon)} />
              </svg>
              {item.name}
            </Link>
          ))}
        </nav>
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-gray-200 mt-auto">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-700">Nonprofit Admin</p>
            <p className="text-xs font-medium text-gray-500">Grant Management</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to get SVG path for icons
const getIconPath = (icon) => {
  switch (icon) {
    case 'grid':
      return "M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zm-10 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z";
    case 'file-text':
      return "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z";
    case 'users':
      return "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z";
    case 'search':
      return "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z";
    case 'chart-bar':
      return "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z";
    case 'pencil':
      return "M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z";
    default:
      return "M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z";
  }
};

export default Sidebar;

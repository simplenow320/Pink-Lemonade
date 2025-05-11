import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const BottomNav = () => {
  const location = useLocation();
  
  const navItems = [
    { name: 'Dashboard', href: '/', icon: 'grid' },
    { name: 'Grants', href: '/grants', icon: 'file-text' },
    { name: 'Org', href: '/organization', icon: 'users' },
    { name: 'Scraper', href: '/scraper', icon: 'search' }
  ];
  
  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="block md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-100 shadow-lg">
      <div className="flex justify-around">
        {navItems.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className={`flex flex-col items-center justify-center py-3 flex-1 transition-colors duration-200 ${
              isActive(item.href) 
                ? 'text-orange-500 border-t-2 border-orange-500 -mt-px pt-[10px]' 
                : 'text-gray-500 hover:text-orange-400'
            }`}
          >
            <svg 
              className={`h-6 w-6 ${isActive(item.href) ? 'text-orange-500' : 'text-gray-500'}`}
              xmlns="http://www.w3.org/2000/svg" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                d={getIconPath(item.icon)} 
              />
            </svg>
            <span className="text-xs mt-1 font-medium">{item.name}</span>
          </Link>
        ))}
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

export default BottomNav;
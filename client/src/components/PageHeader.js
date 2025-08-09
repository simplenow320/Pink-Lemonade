import React from 'react';

/**
 * Page header component with title and optional description and actions
 * @param {Object} props - Component props
 * @param {string} props.title - Page title
 * @param {string} [props.description] - Optional page description
 * @param {React.ReactNode} [props.children] - Optional action buttons or other elements
 */
const PageHeader = ({ title, description, children }) => {
  return (
    <div className="pb-5 border-b border-gray-200 sm:flex sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
          {title}
        </h1>
        {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      </div>
      {children && <div className="mt-3 flex sm:mt-0 sm:ml-4">{children}</div>}
    </div>
  );
};

export default PageHeader;

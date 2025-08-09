import React from 'react';

/**
 * Card component for displaying content in a bordered container
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Card content
 * @param {string} [props.className] - Additional CSS classes
 */
const Card = ({ children, className = '' }) => {
  return <div className={`bg-white shadow rounded-lg p-6 ${className}`}>{children}</div>;
};

export default Card;

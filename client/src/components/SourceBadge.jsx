import React from 'react';
import { ExternalLink } from 'lucide-react';

/**
 * SourceBadge Component
 * Displays a color-coded badge showing the grant source
 * with optional link to the source URL
 */
const SourceBadge = ({ source_name, source_url, className = '' }) => {
  // Map source names to display names and colors
  const getSourceConfig = (sourceName) => {
    if (!sourceName) {
      return {
        displayName: 'Database',
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-700',
        icon: null
      };
    }

    const lowerSource = sourceName.toLowerCase();

    // Federal sources - Blue
    if (lowerSource.includes('sam.gov') || lowerSource.includes('sam gov')) {
      return {
        displayName: 'SAM.gov',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-700',
        icon: '🇺🇸'
      };
    }
    if (lowerSource.includes('federal register')) {
      return {
        displayName: 'Federal Register',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-700',
        icon: '📋'
      };
    }
    if (lowerSource.includes('hhs') || lowerSource.includes('health')) {
      return {
        displayName: 'HHS Grants',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-700',
        icon: '🏥'
      };
    }
    if (lowerSource.includes('education') || lowerSource.includes('ed.gov')) {
      return {
        displayName: 'Education Dept',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-700',
        icon: '🎓'
      };
    }
    if (lowerSource.includes('nsf')) {
      return {
        displayName: 'NSF',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-700',
        icon: '🔬'
      };
    }
    if (lowerSource.includes('usaspending')) {
      return {
        displayName: 'USAspending.gov',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-700',
        icon: '💰'
      };
    }

    // State/Local - Green
    if (lowerSource.includes('socrata') || lowerSource.includes('state') || lowerSource.includes('local')) {
      return {
        displayName: 'State/Local',
        bgColor: 'bg-green-100',
        textColor: 'text-green-700',
        icon: '🏛️'
      };
    }

    // Foundations - Purple
    if (lowerSource.includes('candid') || lowerSource.includes('foundation')) {
      return {
        displayName: 'Foundation',
        bgColor: 'bg-purple-100',
        textColor: 'text-purple-700',
        icon: '🏛️'
      };
    }

    // ProPublica - Orange
    if (lowerSource.includes('propublica')) {
      return {
        displayName: 'ProPublica',
        bgColor: 'bg-orange-100',
        textColor: 'text-orange-700',
        icon: '📰'
      };
    }

    // Default - Gray
    return {
      displayName: sourceName,
      bgColor: 'bg-gray-100',
      textColor: 'text-gray-700',
      icon: null
    };
  };

  const config = getSourceConfig(source_name);

  // If there's a source URL, make it clickable
  if (source_url) {
    return (
      <a
        href={source_url}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor} hover:opacity-80 transition-opacity ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        {config.icon && <span className="text-sm">{config.icon}</span>}
        <span>{config.displayName}</span>
        <ExternalLink size={12} className="opacity-60" />
      </a>
    );
  }

  // Non-clickable badge
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor} ${className}`}>
      {config.icon && <span className="text-sm">{config.icon}</span>}
      <span>{config.displayName}</span>
    </span>
  );
};

export default SourceBadge;

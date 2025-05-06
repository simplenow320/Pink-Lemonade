// Date formatters
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};

export const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Currency formatter
export const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return 'N/A';
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
};

// Get status class for styling
export const getStatusClass = (status) => {
  if (!status) return '';
  
  const statusMap = {
    'Not Started': 'bg-gray-200 text-gray-700',
    'In Progress': 'bg-blue-100 text-blue-800',
    'Submitted': 'bg-yellow-100 text-yellow-800',
    'Won': 'bg-green-100 text-green-800',
    'Declined': 'bg-red-100 text-red-800'
  };
  
  return statusMap[status] || 'bg-gray-100 text-gray-800';
};

// Get date urgency class
export const getDateUrgencyClass = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  const today = new Date();
  const diffDays = Math.ceil((date - today) / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) {
    return 'text-red-600 font-medium';
  } else if (diffDays <= 14) {
    return 'text-yellow-600 font-medium';
  } else {
    return 'text-blue-600';
  }
};

// Get match score class
export const getMatchScoreClass = (score) => {
  if (score === null || score === undefined) return '';
  
  if (score >= 80) {
    return 'text-green-600 font-medium';
  } else if (score >= 50) {
    return 'text-yellow-600 font-medium';
  } else {
    return 'text-gray-600';
  }
};

// Format match score
export const formatMatchScore = (score) => {
  if (score === null || score === undefined) return 'N/A';
  return `${Math.round(score)}%`;
};

// Truncate text
export const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  
  if (text.length <= maxLength) {
    return text;
  }
  
  return text.substring(0, maxLength) + '...';
};

// Format duration
export const formatDuration = (durationString) => {
  if (!durationString) return 'N/A';
  
  // Expected format from the API is like '0:02:45.123456' (h:mm:ss.microseconds)
  // We'll just extract hours, minutes, seconds
  const parts = durationString.split(':');
  
  if (parts.length < 3) return durationString;
  
  const hours = parseInt(parts[0]);
  const minutes = parseInt(parts[1]);
  const seconds = parseInt(parts[2]);
  
  let result = '';
  
  if (hours > 0) {
    result += `${hours} hour${hours !== 1 ? 's' : ''} `;
  }
  
  if (minutes > 0 || hours > 0) {
    result += `${minutes} minute${minutes !== 1 ? 's' : ''} `;
  }
  
  result += `${seconds} second${seconds !== 1 ? 's' : ''}`;
  
  return result;
};

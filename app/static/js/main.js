// Main JavaScript for GrantFlow application

document.addEventListener('DOMContentLoaded', function() {
  console.log('GrantFlow application initialized');
  
  // Initialize UI components if not using React
  initializeComponents();
});

/**
 * Initialize UI components
 */
function initializeComponents() {
  // Initialize date formatting for all date elements
  formatDates();
  
  // Initialize status badges
  initStatusBadges();
  
  // Initialize match score indicators
  initMatchScores();
  
  // Initialize tooltips
  initTooltips();
  
  // Initialize dropdown menus
  initDropdowns();
  
  // Initialize mobile navigation
  initMobileNav();
}

/**
 * Format dates to show relative time and add appropriate classes
 */
function formatDates() {
  const dateElements = document.querySelectorAll('[data-date]');
  
  dateElements.forEach(el => {
    const dateStr = el.getAttribute('data-date');
    if (!dateStr) return;
    
    const date = new Date(dateStr);
    
    // Add formatted date
    el.textContent = formatDate(date);
    
    // Add appropriate class based on date proximity
    const daysUntil = getDaysUntil(date);
    
    if (daysUntil < 0) {
      el.classList.add('date-past');
    } else if (daysUntil <= 14) {
      el.classList.add('date-soon');
    } else {
      el.classList.add('date-future');
    }
  });
}

/**
 * Format date to a readable string
 * @param {Date} date - The date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return date.toLocaleDateString(undefined, options);
}

/**
 * Get days until a date
 * @param {Date} date - The target date
 * @returns {number} Days until the date (negative if in the past)
 */
function getDaysUntil(date) {
  const now = new Date();
  const diffTime = date - now;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
}

/**
 * Initialize status badges with appropriate classes
 */
function initStatusBadges() {
  const statusBadges = document.querySelectorAll('[data-status]');
  
  statusBadges.forEach(badge => {
    const status = badge.getAttribute('data-status');
    if (!status) return;
    
    const statusClass = `status-${status.toLowerCase().replace(/\s+/g, '-')}`;
    badge.classList.add(statusClass);
  });
}

/**
 * Initialize match score indicators
 */
function initMatchScores() {
  const scoreElements = document.querySelectorAll('[data-match-score]');
  
  scoreElements.forEach(el => {
    const score = parseInt(el.getAttribute('data-match-score'));
    if (isNaN(score)) return;
    
    // Add text representation
    el.textContent = `${score}%`;
    
    // Add appropriate class based on score
    if (score >= 80) {
      el.classList.add('match-high');
    } else if (score >= 50) {
      el.classList.add('match-medium');
    } else {
      el.classList.add('match-low');
    }
    
    // If element has a progress bar child, update its width
    const progressBar = el.querySelector('.progress-bar-fill');
    if (progressBar) {
      progressBar.style.width = `${score}%`;
      
      if (score >= 80) {
        progressBar.classList.add('high');
      } else if (score >= 50) {
        progressBar.classList.add('medium');
      } else {
        progressBar.classList.add('low');
      }
    }
  });
}

/**
 * Initialize tooltips
 */
function initTooltips() {
  const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
  
  tooltipTriggers.forEach(trigger => {
    trigger.addEventListener('mouseenter', showTooltip);
    trigger.addEventListener('mouseleave', hideTooltip);
  });
}

/**
 * Show tooltip
 * @param {Event} event - Mouse event
 */
function showTooltip(event) {
  const trigger = event.currentTarget;
  const tooltipText = trigger.getAttribute('data-tooltip');
  
  if (!tooltipText) return;
  
  // Create tooltip element
  const tooltip = document.createElement('div');
  tooltip.className = 'tooltip';
  tooltip.textContent = tooltipText;
  
  // Position tooltip
  const rect = trigger.getBoundingClientRect();
  tooltip.style.top = `${rect.top - 10}px`;
  tooltip.style.left = `${rect.left + rect.width / 2}px`;
  
  // Add tooltip to body
  document.body.appendChild(tooltip);
  
  // Store reference to tooltip
  trigger.tooltip = tooltip;
  
  // Animate in
  setTimeout(() => {
    tooltip.classList.add('tooltip-visible');
  }, 10);
}

/**
 * Hide tooltip
 * @param {Event} event - Mouse event
 */
function hideTooltip(event) {
  const trigger = event.currentTarget;
  const tooltip = trigger.tooltip;
  
  if (!tooltip) return;
  
  // Animate out
  tooltip.classList.remove('tooltip-visible');
  
  // Remove tooltip after animation
  setTimeout(() => {
    if (tooltip.parentNode) {
      tooltip.parentNode.removeChild(tooltip);
    }
    trigger.tooltip = null;
  }, 200);
}

/**
 * Initialize dropdown menus
 */
function initDropdowns() {
  const dropdownTriggers = document.querySelectorAll('[data-dropdown]');
  
  dropdownTriggers.forEach(trigger => {
    trigger.addEventListener('click', toggleDropdown);
  });
  
  // Close dropdowns when clicking outside
  document.addEventListener('click', event => {
    const isDropdownClick = event.target.closest('[data-dropdown]');
    
    if (!isDropdownClick) {
      // Close all open dropdowns
      const openDropdowns = document.querySelectorAll('.dropdown-menu.active');
      openDropdowns.forEach(dropdown => {
        dropdown.classList.remove('active');
      });
    }
  });
}

/**
 * Toggle dropdown menu
 * @param {Event} event - Click event
 */
function toggleDropdown(event) {
  event.preventDefault();
  event.stopPropagation();
  
  const trigger = event.currentTarget;
  const targetId = trigger.getAttribute('data-dropdown');
  const dropdown = document.getElementById(targetId);
  
  if (!dropdown) return;
  
  // Toggle active class
  dropdown.classList.toggle('active');
}

/**
 * Initialize mobile navigation
 */
function initMobileNav() {
  const menuToggle = document.querySelector('#mobile-menu-toggle');
  const mobileMenu = document.querySelector('#mobile-menu');
  
  if (!menuToggle || !mobileMenu) return;
  
  menuToggle.addEventListener('click', () => {
    mobileMenu.classList.toggle('active');
    menuToggle.setAttribute('aria-expanded', 
      menuToggle.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
    );
  });
}

/**
 * Format currency
 * @param {number} amount - The amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
  if (!amount && amount !== 0) return 'N/A';
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
}

/**
 * Create loading spinner
 * @returns {HTMLElement} Spinner element
 */
function createSpinner() {
  const spinner = document.createElement('div');
  spinner.className = 'spinner';
  return spinner;
}

/**
 * Show loading state on an element
 * @param {HTMLElement} element - Element to show loading state on
 * @param {string} text - Optional loading text
 */
function showLoading(element, text = 'Loading...') {
  // Save original content
  element.dataset.originalContent = element.innerHTML;
  
  // Clear contents
  element.innerHTML = '';
  
  // Add spinner
  const spinner = createSpinner();
  element.appendChild(spinner);
  
  // Add text if provided
  if (text) {
    const textNode = document.createTextNode(' ' + text);
    element.appendChild(textNode);
  }
  
  // Add loading class
  element.classList.add('loading');
}

/**
 * Hide loading state on an element
 * @param {HTMLElement} element - Element to hide loading state on
 */
function hideLoading(element) {
  // Restore original content
  if (element.dataset.originalContent) {
    element.innerHTML = element.dataset.originalContent;
    delete element.dataset.originalContent;
  }
  
  // Remove loading class
  element.classList.remove('loading');
}

/**
 * Show alert message
 * @param {string} message - Message to display
 * @param {string} type - Alert type (info, success, warning, danger)
 * @param {number} duration - Duration in milliseconds (0 for no auto-hide)
 */
function showAlert(message, type = 'info', duration = 5000) {
  const alertContainer = document.querySelector('#alert-container');
  
  if (!alertContainer) {
    // Create alert container if it doesn't exist
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '1000';
    document.body.appendChild(container);
  }
  
  // Create alert element
  const alert = document.createElement('div');
  alert.className = `alert alert-${type}`;
  alert.textContent = message;
  
  // Add close button
  const closeBtn = document.createElement('button');
  closeBtn.className = 'alert-close';
  closeBtn.innerHTML = '&times;';
  closeBtn.addEventListener('click', () => {
    if (alert.parentNode) {
      alert.parentNode.removeChild(alert);
    }
  });
  alert.appendChild(closeBtn);
  
  // Add to container
  alertContainer.appendChild(alert);
  
  // Auto-hide after duration
  if (duration > 0) {
    setTimeout(() => {
      if (alert.parentNode) {
        alert.classList.add('alert-hiding');
        setTimeout(() => {
          if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
          }
        }, 300);
      }
    }, duration);
  }
  
  return alert;
}

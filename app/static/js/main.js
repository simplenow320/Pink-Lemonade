// Main JavaScript for GrantFlow application

document.addEventListener('DOMContentLoaded', function() {
  console.log('GrantFlow application initialized');
  
  // Initialize UI components if not using React
  initializeComponents();
  
  // Initialize API event listeners
  initApiEventListeners();
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

/**
 * Initialize API event listeners
 */
function initApiEventListeners() {
  // Initialize scrape button
  initScrapeButton();
  
  // Initialize match button
  initMatchButton();
  
  // Initialize write button
  initWriteButton();
  
  // Initialize report button
  initReportButton();
}

/**
 * Initialize the scrape button functionality
 */
function initScrapeButton() {
  const scrapeButton = document.querySelector('#scrape-button');
  if (!scrapeButton) return;
  
  scrapeButton.addEventListener('click', function(event) {
    event.preventDefault();
    
    // Show loading state
    showLoading(scrapeButton, 'Scraping...');
    
    // Call the scrape API
    fetch('/api/scraper/scrape')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to scrape grants');
        }
        return response.json();
      })
      .then(data => {
        // Update grants table
        updateGrantsTable(data);
        
        // Show success message
        showAlert(`Successfully scraped ${data.length} grants`, 'success');
      })
      .catch(error => {
        console.error('Error scraping grants:', error);
        showAlert('Failed to scrape grants: ' + error.message, 'danger');
      })
      .finally(() => {
        // Hide loading state
        hideLoading(scrapeButton);
      });
  });
}

/**
 * Update the grants table with new data
 * @param {Array} grants - Array of grant objects
 */
function updateGrantsTable(grants) {
  const grantsTableBody = document.querySelector('#grants-table tbody');
  if (!grantsTableBody) return;
  
  // Clear existing rows
  grantsTableBody.innerHTML = '';
  
  // Add new rows
  grants.forEach(grant => {
    const row = document.createElement('tr');
    
    // Create grant row (adjust based on your actual HTML structure)
    row.innerHTML = `
      <td>
        <input type="checkbox" class="grant-checkbox" value="${grant.id}" />
      </td>
      <td>${grant.title}</td>
      <td>${grant.funder}</td>
      <td>
        <span data-date="${grant.due_date}">${formatDate(new Date(grant.due_date))}</span>
      </td>
      <td>
        <span data-status="${grant.status}" class="status-badge">${grant.status}</span>
      </td>
      <td>
        <span data-match-score="${grant.match_score}" class="match-score">
          <div class="progress-bar">
            <div class="progress-bar-fill" style="width: ${grant.match_score}%"></div>
          </div>
          ${grant.match_score}%
        </span>
      </td>
      <td>
        <button class="btn btn-sm btn-outline view-grant" data-grant-id="${grant.id}">View</button>
      </td>
    `;
    
    grantsTableBody.appendChild(row);
  });
  
  // Re-initialize UI components for the new elements
  formatDates();
  initStatusBadges();
  initMatchScores();
}

/**
 * Initialize the match button functionality
 */
function initMatchButton() {
  const matchButton = document.querySelector('#match-button');
  if (!matchButton) return;
  
  matchButton.addEventListener('click', function(event) {
    event.preventDefault();
    
    // Get selected grants
    const selectedGrants = getSelectedGrants();
    if (selectedGrants.length === 0) {
      showAlert('Please select at least one grant to match', 'warning');
      return;
    }
    
    // Show loading state
    showLoading(matchButton, 'Matching...');
    
    // Process each selected grant
    const matchPromises = selectedGrants.map(grantId => {
      return fetch('/api/grants/match', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ grant_id: grantId })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Failed to match grant ${grantId}`);
        }
        return response.json();
      });
    });
    
    // Wait for all matches to complete
    Promise.all(matchPromises)
      .then(results => {
        // Update match table or display
        updateMatchResults(results);
        
        // Show success message
        showAlert(`Successfully matched ${results.length} grants`, 'success');
      })
      .catch(error => {
        console.error('Error matching grants:', error);
        showAlert('Failed to match grants: ' + error.message, 'danger');
      })
      .finally(() => {
        // Hide loading state
        hideLoading(matchButton);
      });
  });
}

/**
 * Get selected grant IDs from checkboxes
 * @returns {Array} Array of selected grant IDs
 */
function getSelectedGrants() {
  const checkboxes = document.querySelectorAll('.grant-checkbox:checked');
  return Array.from(checkboxes).map(checkbox => checkbox.value);
}

/**
 * Update match results in the UI
 * @param {Array} results - Array of match results
 */
function updateMatchResults(results) {
  const matchTableBody = document.querySelector('#match-table tbody');
  if (!matchTableBody) return;
  
  // Clear existing rows
  matchTableBody.innerHTML = '';
  
  // Add new rows
  results.forEach(result => {
    const row = document.createElement('tr');
    
    // Create match row (adjust based on your actual HTML structure)
    row.innerHTML = `
      <td>${result.grant_title || 'Unknown'}</td>
      <td>
        <span data-match-score="${result.match_score}" class="match-score">
          <div class="progress-bar">
            <div class="progress-bar-fill" style="width: ${result.match_score}%"></div>
          </div>
          ${result.match_score}%
        </span>
      </td>
      <td>${result.match_explanation || ''}</td>
    `;
    
    matchTableBody.appendChild(row);
  });
  
  // Re-initialize UI components for the new elements
  initMatchScores();
}

/**
 * Initialize the write button functionality
 */
function initWriteButton() {
  const writeButton = document.querySelector('#write-button');
  if (!writeButton) return;
  
  writeButton.addEventListener('click', function(event) {
    event.preventDefault();
    
    // Get selected grant
    const selectedGrants = getSelectedGrants();
    if (selectedGrants.length !== 1) {
      showAlert('Please select exactly one grant to generate a narrative', 'warning');
      return;
    }
    
    const grantId = selectedGrants[0];
    
    // Get selected section type
    const sectionTypeSelect = document.querySelector('#section-type-select');
    const sectionType = sectionTypeSelect ? sectionTypeSelect.value : 'overview';
    
    // Show loading state
    showLoading(writeButton, 'Generating narrative...');
    
    // Call the write API
    fetch('/api/grants/write', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        grant_id: grantId,
        section_type: sectionType
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to generate narrative');
      }
      return response.json();
    })
    .then(data => {
      // Display the narrative
      displayNarrative(data);
      
      // Show success message
      showAlert('Successfully generated narrative', 'success');
    })
    .catch(error => {
      console.error('Error generating narrative:', error);
      showAlert('Failed to generate narrative: ' + error.message, 'danger');
    })
    .finally(() => {
      // Hide loading state
      hideLoading(writeButton);
    });
  });
}

/**
 * Display the generated narrative
 * @param {Object} data - Narrative data
 */
function displayNarrative(data) {
  const narrativeContainer = document.querySelector('#narrative-container');
  if (!narrativeContainer) return;
  
  // Update narrative content
  narrativeContainer.innerHTML = '';
  
  // Create title
  const title = document.createElement('h3');
  title.textContent = data.section_title || 'Generated Narrative';
  narrativeContainer.appendChild(title);
  
  // Create content
  const content = document.createElement('div');
  content.className = 'narrative-content';
  content.innerHTML = data.content || '';
  narrativeContainer.appendChild(content);
  
  // Create metadata if available
  if (data.tips && data.tips.length > 0) {
    const tipsTitle = document.createElement('h4');
    tipsTitle.textContent = 'Writing Tips';
    narrativeContainer.appendChild(tipsTitle);
    
    const tipsList = document.createElement('ul');
    tipsList.className = 'tips-list';
    
    data.tips.forEach(tip => {
      const tipItem = document.createElement('li');
      tipItem.textContent = tip;
      tipsList.appendChild(tipItem);
    });
    
    narrativeContainer.appendChild(tipsList);
  }
  
  // Show the container
  narrativeContainer.style.display = 'block';
}

/**
 * Initialize the report button functionality
 */
function initReportButton() {
  const reportButton = document.querySelector('#report-button');
  if (!reportButton) return;
  
  reportButton.addEventListener('click', function(event) {
    event.preventDefault();
    
    // Show loading state
    showLoading(reportButton, 'Generating report...');
    
    // Call the report API
    fetch('/api/analytics/report')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to generate report');
        }
        return response.json();
      })
      .then(data => {
        // Display the report
        displayReport(data);
        
        // Show success message
        showAlert('Successfully generated analytics report', 'success');
      })
      .catch(error => {
        console.error('Error generating report:', error);
        showAlert('Failed to generate report: ' + error.message, 'danger');
      })
      .finally(() => {
        // Hide loading state
        hideLoading(reportButton);
      });
  });
}

/**
 * Display the generated report
 * @param {Object} data - Report data
 */
function displayReport(data) {
  const reportContainer = document.querySelector('#report-container');
  if (!reportContainer) return;
  
  // Clear existing content
  reportContainer.innerHTML = '';
  
  // Add summary text
  if (data.summary_text) {
    const summary = document.createElement('div');
    summary.className = 'report-summary';
    summary.textContent = data.summary_text;
    reportContainer.appendChild(summary);
  }
  
  // Add chart if chart_data is available
  if (data.chart_data && data.chart_data.length > 0) {
    const chartContainer = document.createElement('div');
    chartContainer.className = 'chart-container';
    reportContainer.appendChild(chartContainer);
    
    // Create canvas for chart
    const canvas = document.createElement('canvas');
    canvas.id = 'report-chart';
    chartContainer.appendChild(canvas);
    
    // Create chart
    if (typeof Chart !== 'undefined') {
      createReportChart(canvas, data.chart_data);
    } else {
      console.warn('Chart.js is not available');
    }
  }
  
  // Add chart image if base64 is available
  if (data.chart_image_base64) {
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${data.chart_image_base64}`;
    img.alt = 'Analytics Report Chart';
    img.className = 'report-chart-image';
    reportContainer.appendChild(img);
  }
  
  // Show the container
  reportContainer.style.display = 'block';
}

/**
 * Create a chart using Chart.js
 * @param {HTMLCanvasElement} canvas - Canvas element
 * @param {Array} chartData - Chart data
 */
function createReportChart(canvas, chartData) {
  // Extract labels and data
  const labels = chartData.map(item => item.focus_area);
  const data = chartData.map(item => item.success_rate);
  
  // Create chart
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Success Rate (%)',
        data: data,
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      }
    }
  });
}

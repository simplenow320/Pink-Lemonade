// Grants and Applications Shared JavaScript
// Environment toggle: set to 'API' to use backend endpoints, 'MOCK' for local data
const DATA_MODE = 'MOCK'; // TODO: Change to 'API' when backend is ready

// Global state
let config = {};
let allGrants = [];
let filteredGrants = [];
let currentPage = 1;
let currentPageType = 'grants'; // 'grants' or 'applications'
let currentGrant = null;
let currentTab = 'overview';
const grantsPerPage = 10;

// API endpoints (for when DATA_MODE = 'API')
const API_ENDPOINTS = {
    grants: '/api/grants',
    grant: (id) => `/api/grants/${id}`,
    notes: (id) => `/api/grants/${id}/notes`,
    contacts: (id) => `/api/grants/${id}/contacts`,
    attachments: (id) => `/api/grants/${id}/attachments`
};

// Initialize grants page
async function initGrantsPage(pageType) {
    currentPageType = pageType;
    
    try {
        // Load configuration
        const configResponse = await fetch('/static/grants-config.json');
        config = await configResponse.json();
        
        // Load grants data
        await loadGrantsData();
        
        // Setup page
        setupPage();
        populateFilters();
        applyFilters();
        
        // Setup event listeners
        setupEventListeners();
        
    } catch (error) {
        console.error('Error initializing grants page:', error);
        showError('Failed to load grants data. Please try again later.');
    }
}

// Load grants data (API or Mock)
async function loadGrantsData() {
    if (DATA_MODE === 'API') {
        // TODO: Replace with actual API call
        const response = await fetch(API_ENDPOINTS.grants);
        const data = await response.json();
        allGrants = data.grants || [];
    } else {
        // Load mock data
        const response = await fetch('/static/grants-mock-data.json');
        const data = await response.json();
        allGrants = data.grants || [];
    }
}

// Setup page specific elements
function setupPage() {
    // Update page title
    const title = currentPageType === 'grants' ? 
        config.labels.grants_page_title : 
        config.labels.applications_page_title;
    document.getElementById('page-title').textContent = title;
    
    // Update search placeholder
    const searchInput = document.getElementById('search-input');
    searchInput.placeholder = config.labels.search_placeholder;
    
    // Update navigation active state
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    const navId = currentPageType === 'grants' ? 'grants-nav' : 'applications-nav';
    const navElement = document.getElementById(navId);
    if (navElement) navElement.classList.add('active');
}

// Populate filter dropdowns
function populateFilters() {
    // Status filter
    const statusFilter = document.getElementById('status-filter');
    statusFilter.innerHTML = '<option value="">All Statuses</option>';
    config.filters.status_options.forEach(status => {
        const option = document.createElement('option');
        option.value = status;
        option.textContent = config.statuses[status].label;
        statusFilter.appendChild(option);
    });
    
    // Deadline filter
    const deadlineFilter = document.getElementById('deadline-filter');
    deadlineFilter.innerHTML = '<option value="">All Deadlines</option>';
    config.filters.deadline_windows.forEach(window => {
        const option = document.createElement('option');
        option.value = window.value;
        option.textContent = window.label;
        deadlineFilter.appendChild(option);
    });
    
    // Geography filter
    const geoFilter = document.getElementById('geography-filter');
    geoFilter.innerHTML = '<option value="">All Locations</option>';
    config.filters.geography_options.forEach(geo => {
        const option = document.createElement('option');
        option.value = geo;
        option.textContent = geo;
        geoFilter.appendChild(option);
    });
    
    // Apply default filters for applications page
    if (currentPageType === 'applications' && config.default_filters.applications_page.status) {
        statusFilter.value = config.default_filters.applications_page.status[0];
    }
}

// Apply filters and search
function applyFilters() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const statusFilter = document.getElementById('status-filter').value;
    const deadlineFilter = document.getElementById('deadline-filter').value;
    const geoFilter = document.getElementById('geography-filter').value;
    const sortBy = document.getElementById('sort-select').value;
    
    // Start with all grants
    filteredGrants = [...allGrants];
    
    // Apply page-specific default filters
    if (currentPageType === 'applications') {
        const defaultStatuses = config.default_filters.applications_page.status;
        if (defaultStatuses && !statusFilter) {
            filteredGrants = filteredGrants.filter(grant => 
                defaultStatuses.includes(grant.status)
            );
        }
    }
    
    // Apply search filter
    if (searchTerm) {
        filteredGrants = filteredGrants.filter(grant => {
            const searchableText = (
                grant.title + ' ' + 
                (grant.funder || '') + ' ' + 
                (grant.tags || []).join(' ')
            ).toLowerCase();
            return searchableText.includes(searchTerm);
        });
    }
    
    // Apply status filter
    if (statusFilter) {
        filteredGrants = filteredGrants.filter(grant => grant.status === statusFilter);
    }
    
    // Apply deadline filter
    if (deadlineFilter) {
        const days = parseInt(deadlineFilter);
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() + days);
        
        filteredGrants = filteredGrants.filter(grant => {
            if (!grant.deadline) return false;
            const deadline = new Date(grant.deadline);
            return deadline <= cutoffDate;
        });
    }
    
    // Apply geography filter
    if (geoFilter) {
        filteredGrants = filteredGrants.filter(grant => grant.geography === geoFilter);
    }
    
    // Sort results
    filteredGrants.sort((a, b) => {
        switch (sortBy) {
            case 'deadline':
                if (!a.deadline && !b.deadline) return 0;
                if (!a.deadline) return 1;
                if (!b.deadline) return -1;
                return new Date(a.deadline) - new Date(b.deadline);
            case 'amount':
                return (b.amountMax || 0) - (a.amountMax || 0);
            case 'fitScore':
                return (b.fitScore || 0) - (a.fitScore || 0);
            case 'updatedAt':
            default:
                return new Date(b.updatedAt) - new Date(a.updatedAt);
        }
    });
    
    currentPage = 1;
    displayGrants();
}

// Display grants in table
function displayGrants() {
    const tbody = document.getElementById('grants-table-body');
    const startIndex = (currentPage - 1) * grantsPerPage;
    const endIndex = startIndex + grantsPerPage;
    const pageGrants = filteredGrants.slice(startIndex, endIndex);
    
    if (pageGrants.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                    ${config.labels.no_results}
                </td>
            </tr>
        `;
        updatePagination();
        return;
    }
    
    tbody.innerHTML = pageGrants.map(grant => {
        const statusConfig = config.statuses[grant.status];
        const deadlineDate = grant.deadline ? new Date(grant.deadline) : null;
        const formattedDeadline = deadlineDate ? 
            deadlineDate.toLocaleDateString() : 'No deadline';
        
        const amount = grant.amountMin && grant.amountMax ? 
            `$${formatNumber(grant.amountMin)} - $${formatNumber(grant.amountMax)}` :
            grant.amountMax ? `Up to $${formatNumber(grant.amountMax)}` : 'Amount TBD';
        
        const updatedDate = new Date(grant.updatedAt).toLocaleDateString();
        
        return `
            <tr class="grant-row" onclick="openGrantDetail('${grant.id}')">
                <td class="px-6 py-4">
                    <div>
                        <div class="font-medium text-gray-900">${grant.title}</div>
                        <div class="text-sm text-gray-500">${grant.funder || 'Unknown Funder'}</div>
                        <div class="mt-1">
                            ${(grant.tags || []).slice(0, 3).map(tag => 
                                `<span class="tag">${tag}</span>`
                            ).join('')}
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="status-pill" style="background-color: ${statusConfig.color}">
                        ${statusConfig.label}
                    </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-900">
                    ${amount}
                </td>
                <td class="px-6 py-4 text-sm text-gray-900">
                    ${formattedDeadline}
                </td>
                <td class="px-6 py-4">
                    ${grant.fitScore ? `<span class="fit-score">${grant.fitScore.toFixed(1)}</span>` : '-'}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                    ${updatedDate}
                </td>
            </tr>
        `;
    }).join('');
    
    updatePagination();
}

// Update pagination
function updatePagination() {
    const totalPages = Math.ceil(filteredGrants.length / grantsPerPage);
    const startIndex = (currentPage - 1) * grantsPerPage;
    const endIndex = Math.min(startIndex + grantsPerPage, filteredGrants.length);
    
    // Update pagination info
    document.getElementById('pagination-start').textContent = filteredGrants.length > 0 ? startIndex + 1 : 0;
    document.getElementById('pagination-end').textContent = endIndex;
    document.getElementById('pagination-total').textContent = filteredGrants.length;
    
    // Update pagination buttons
    const container = document.getElementById('pagination-buttons');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    if (currentPage > 1) {
        html += `<button class="btn-secondary" onclick="changePage(${currentPage - 1})">Previous</button>`;
    }
    
    // Page numbers (show up to 5 pages)
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            html += `<button class="btn-primary">${i}</button>`;
        } else {
            html += `<button class="btn-secondary" onclick="changePage(${i})">${i}</button>`;
        }
    }
    
    // Next button
    if (currentPage < totalPages) {
        html += `<button class="btn-secondary" onclick="changePage(${currentPage + 1})">Next</button>`;
    }
    
    container.innerHTML = html;
}

// Change page
function changePage(page) {
    currentPage = page;
    displayGrants();
}

// Clear all filters
function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('status-filter').value = '';
    document.getElementById('deadline-filter').value = '';
    document.getElementById('geography-filter').value = '';
    document.getElementById('sort-select').value = 'updatedAt';
    applyFilters();
}

// Open grant detail panel
function openGrantDetail(grantId) {
    currentGrant = allGrants.find(g => g.id === grantId);
    if (!currentGrant) return;
    
    document.getElementById('detail-title').textContent = currentGrant.title;
    document.getElementById('detail-overlay').classList.add('visible');
    document.getElementById('detail-panel').classList.add('open');
    
    // Switch to overview tab
    switchTab('overview');
}

// Close detail panel
function closeDetailPanel() {
    document.getElementById('detail-overlay').classList.remove('visible');
    document.getElementById('detail-panel').classList.remove('open');
    currentGrant = null;
}

// Switch tabs in detail panel
function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Load tab content
    const content = document.getElementById('tab-content');
    
    switch (tabName) {
        case 'overview':
            content.innerHTML = renderOverviewTab();
            break;
        case 'notes':
            content.innerHTML = renderNotesTab();
            break;
        case 'contacts':
            content.innerHTML = renderContactsTab();
            break;
        case 'files':
            content.innerHTML = renderFilesTab();
            break;
        case 'activity':
            content.innerHTML = renderActivityTab();
            break;
    }
}

// Render overview tab
function renderOverviewTab() {
    if (!currentGrant) return '';
    
    const statusOrder = ['idea', 'researching', 'drafting', 'submitted', 'awarded', 'declined'];
    const currentIndex = statusOrder.indexOf(currentGrant.status);
    
    const amount = currentGrant.amountMin && currentGrant.amountMax ? 
        `$${formatNumber(currentGrant.amountMin)} - $${formatNumber(currentGrant.amountMax)}` :
        currentGrant.amountMax ? `Up to $${formatNumber(currentGrant.amountMax)}` : 'Amount TBD';
    
    const deadline = currentGrant.deadline ? 
        new Date(currentGrant.deadline).toLocaleDateString() : 'No deadline';
    
    return `
        <div class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Funder</h3>
                    <p class="text-gray-900">${currentGrant.funder || 'Unknown'}</p>
                </div>
                <div>
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Amount</h3>
                    <p class="text-gray-900">${amount}</p>
                </div>
                <div>
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Deadline</h3>
                    <p class="text-gray-900">${deadline}</p>
                </div>
                <div>
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Geography</h3>
                    <p class="text-gray-900">${currentGrant.geography || 'Not specified'}</p>
                </div>
            </div>
            
            ${currentGrant.link ? `
                <div>
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Grant Link</h3>
                    <a href="${currentGrant.link}" target="_blank" class="text-pink-600 hover:underline">
                        View Grant Details →
                    </a>
                </div>
            ` : ''}
            
            <div>
                <h3 class="text-sm font-medium text-gray-500 mb-2">Status Timeline</h3>
                <div class="status-timeline">
                    ${statusOrder.map((status, index) => {
                        const statusConfig = config.statuses[status];
                        let stepClass = '';
                        if (index < currentIndex) stepClass = 'completed';
                        else if (index === currentIndex) stepClass = 'current';
                        
                        return `
                            <div class="status-step ${stepClass}" onclick="updateGrantStatus('${status}')">
                                <div class="status-circle ${stepClass}">
                                    ${index < currentIndex ? '✓' : index + 1}
                                </div>
                                <div class="text-xs text-gray-600">${statusConfig.label}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
            
            <div>
                <h3 class="text-sm font-medium text-gray-500 mb-2">Eligibility Requirements</h3>
                <div class="bg-gray-50 p-4 rounded-lg">
                    <p class="text-sm text-gray-700">
                        ${currentGrant.eligibility || 'No eligibility requirements specified.'}
                    </p>
                </div>
            </div>
            
            ${currentGrant.tags && currentGrant.tags.length > 0 ? `
                <div>
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Tags</h3>
                    <div>
                        ${currentGrant.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

// Render notes tab
function renderNotesTab() {
    if (!currentGrant) return '';
    
    const notes = currentGrant.notes || [];
    
    return `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Notes</h3>
                <button class="btn-primary" onclick="addNote()">Add Note</button>
            </div>
            
            <div class="space-y-4">
                ${notes.length === 0 ? `
                    <p class="text-gray-500 text-center py-8">No notes yet. Add a note to track your progress.</p>
                ` : notes.map(note => `
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <div class="flex justify-between items-start mb-2">
                            <div class="text-sm text-gray-600">
                                ${note.author || 'Unknown'} • ${new Date(note.createdAt).toLocaleString()}
                            </div>
                        </div>
                        <p class="text-gray-900">${note.body}</p>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Render contacts tab
function renderContactsTab() {
    if (!currentGrant) return '';
    
    const contacts = currentGrant.contacts || [];
    
    return `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Contacts</h3>
                <button class="btn-primary" onclick="addContact()">Add Contact</button>
            </div>
            
            <div class="space-y-4">
                ${contacts.length === 0 ? `
                    <p class="text-gray-500 text-center py-8">No contacts yet. Add contact information for this grant.</p>
                ` : contacts.map(contact => `
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <h4 class="font-medium text-gray-900">${contact.name}</h4>
                                ${contact.role ? `<p class="text-sm text-gray-600">${contact.role}</p>` : ''}
                            </div>
                            <div class="space-y-1">
                                ${contact.email ? `
                                    <p class="text-sm">
                                        <a href="mailto:${contact.email}" class="text-pink-600 hover:underline">
                                            ${contact.email}
                                        </a>
                                    </p>
                                ` : ''}
                                ${contact.phone ? `
                                    <p class="text-sm text-gray-600">${contact.phone}</p>
                                ` : ''}
                            </div>
                        </div>
                        ${contact.notes ? `
                            <div class="mt-3 pt-3 border-t border-gray-200">
                                <p class="text-sm text-gray-700">${contact.notes}</p>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Render files tab
function renderFilesTab() {
    if (!currentGrant) return '';
    
    const attachments = currentGrant.attachments || [];
    
    return `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Files & Attachments</h3>
                <button class="btn-primary" onclick="uploadFile()">Upload File</button>
            </div>
            
            <div class="space-y-4">
                ${attachments.length === 0 ? `
                    <p class="text-gray-500 text-center py-8">No files uploaded. Add documents related to this grant.</p>
                ` : attachments.map(file => `
                    <div class="bg-gray-50 p-4 rounded-lg flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <div class="p-2 bg-gray-200 rounded">
                                <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                            </div>
                            <div>
                                <h4 class="font-medium text-gray-900">${file.name}</h4>
                                <p class="text-sm text-gray-500">
                                    ${file.size ? formatFileSize(file.size) : 'Unknown size'}
                                    ${file.note ? ` • ${file.note}` : ''}
                                </p>
                            </div>
                        </div>
                        <button class="text-gray-400 hover:text-gray-600">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
                            </svg>
                        </button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Render activity tab
function renderActivityTab() {
    if (!currentGrant) return '';
    
    // Generate activity log from grant data
    const activities = [];
    
    // Add creation activity
    activities.push({
        type: 'created',
        timestamp: currentGrant.createdAt,
        description: 'Grant record created'
    });
    
    // Add notes as activities
    if (currentGrant.notes) {
        currentGrant.notes.forEach(note => {
            activities.push({
                type: 'note',
                timestamp: note.createdAt,
                description: `Note added: ${note.body.substring(0, 50)}...`,
                author: note.author
            });
        });
    }
    
    // Add last update
    if (currentGrant.updatedAt !== currentGrant.createdAt) {
        activities.push({
            type: 'updated',
            timestamp: currentGrant.updatedAt,
            description: 'Grant record updated'
        });
    }
    
    // Sort by timestamp
    activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    return `
        <div class="space-y-6">
            <h3 class="text-lg font-medium">Activity Log</h3>
            
            <div class="space-y-4">
                ${activities.length === 0 ? `
                    <p class="text-gray-500 text-center py-8">No activity recorded yet.</p>
                ` : activities.map(activity => `
                    <div class="flex items-start space-x-3">
                        <div class="flex-shrink-0 w-2 h-2 bg-gray-400 rounded-full mt-2"></div>
                        <div class="min-w-0 flex-1">
                            <p class="text-sm text-gray-900">${activity.description}</p>
                            <p class="text-xs text-gray-500">
                                ${new Date(activity.timestamp).toLocaleString()}
                                ${activity.author ? ` by ${activity.author}` : ''}
                            </p>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Setup event listeners
function setupEventListeners() {
    // Search input
    document.getElementById('search-input').addEventListener('input', debounce(applyFilters, 300));
    
    // Filter selects
    document.getElementById('status-filter').addEventListener('change', applyFilters);
    document.getElementById('deadline-filter').addEventListener('change', applyFilters);
    document.getElementById('geography-filter').addEventListener('change', applyFilters);
    document.getElementById('sort-select').addEventListener('change', applyFilters);
    
    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('mobile-open');
        });
    }
    
    // Close detail panel on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && document.getElementById('detail-panel').classList.contains('open')) {
            closeDetailPanel();
        }
    });
}

// Placeholder functions for grant management
function openAddGrantModal() {
    alert('Add Grant functionality will be implemented in the next phase.');
}

function updateGrantStatus(status) {
    if (!currentGrant) return;
    
    const confirmed = confirm(`Update status to "${config.statuses[status].label}"?`);
    if (confirmed) {
        currentGrant.status = status;
        currentGrant.updatedAt = new Date().toISOString();
        
        // TODO: API call to update grant
        if (DATA_MODE === 'API') {
            // updateGrantAPI(currentGrant.id, { status });
        }
        
        // Refresh view
        applyFilters();
        switchTab('overview'); // Refresh overview to show new status
        
        showSuccess(`Status updated to ${config.statuses[status].label}`);
    }
}

function addNote() {
    const noteText = prompt('Enter your note:');
    if (noteText && noteText.trim()) {
        const newNote = {
            id: `note-${Date.now()}`,
            body: noteText.trim(),
            author: 'Current User', // TODO: Get from session
            createdAt: new Date().toISOString()
        };
        
        currentGrant.notes = currentGrant.notes || [];
        currentGrant.notes.push(newNote);
        currentGrant.updatedAt = new Date().toISOString();
        
        // TODO: API call to add note
        if (DATA_MODE === 'API') {
            // addNoteAPI(currentGrant.id, newNote);
        }
        
        switchTab('notes'); // Refresh notes tab
        showSuccess('Note added successfully');
    }
}

function addContact() {
    // TODO: Open contact form modal
    alert('Add Contact functionality will be implemented with a proper form modal.');
}

function uploadFile() {
    // TODO: Open file upload modal (UI only - no actual file storage)
    alert('File upload functionality will be implemented with a proper upload interface.');
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showSuccess(message) {
    // TODO: Implement proper toast notification
    console.log('Success:', message);
}

function showError(message) {
    // TODO: Implement proper error notification
    console.error('Error:', message);
}

// Export functions for global access
window.initGrantsPage = initGrantsPage;
window.openGrantDetail = openGrantDetail;
window.closeDetailPanel = closeDetailPanel;
window.switchTab = switchTab;
window.changePage = changePage;
window.clearFilters = clearFilters;
window.openAddGrantModal = openAddGrantModal;
window.updateGrantStatus = updateGrantStatus;
window.addNote = addNote;
window.addContact = addContact;
window.uploadFile = uploadFile;
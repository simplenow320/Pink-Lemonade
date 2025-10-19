// Discovery and Watchlists JavaScript
let currentTab = 'opportunities';
let opportunities = [];
let watchlists = [];
let DATA_MODE = 'API'; // Toggle between 'API' and 'MOCK'

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadOpportunities();
    loadWatchlists();
});

// Switch tabs
function switchTab(tab) {
    currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    
    // Show/hide tab content
    if (tab === 'opportunities') {
        document.getElementById('opportunities-tab').classList.remove('hidden');
        document.getElementById('watchlists-tab').classList.add('hidden');
    } else {
        document.getElementById('opportunities-tab').classList.add('hidden');
        document.getElementById('watchlists-tab').classList.remove('hidden');
    }
}

// Load latest opportunities
async function loadOpportunities() {
    try {
        let data;
        
        if (DATA_MODE === 'API') {
            const response = await fetch('/api/grants/');
            data = await response.json();
        } else {
            // Mock data fallback
            data = {
                success: true,
                grants: getMockOpportunities()
            };
        }
        
        if (data.success) {
            opportunities = data.grants || [];
            displayOpportunities();
        }
    } catch (error) {
        console.error('Error loading opportunities:', error);
        opportunities = getMockOpportunities();
        displayOpportunities();
    }
}

// Display opportunities
function displayOpportunities() {
    const container = document.getElementById('opportunities-list');
    const count = document.getElementById('opportunity-count');
    
    count.textContent = `${opportunities.length} opportunities`;
    
    if (opportunities.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-600">
                No new opportunities found. Run discovery connectors to fetch latest grants.
            </div>
        `;
        return;
    }
    
    container.innerHTML = opportunities.map(grant => {
        const deadline = grant.deadline ? new Date(grant.deadline).toLocaleDateString() : 'No deadline';
        const amount = grant.amount_min && grant.amount_max ? 
            `$${formatNumber(grant.amount_min)} - $${formatNumber(grant.amount_max)}` :
            grant.amount_max ? `Up to $${formatNumber(grant.amount_max)}` : 
            grant.amount ? `$${formatNumber(grant.amount)}` : 'Amount TBD';
        
        return `
            <div class="grant-item">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <h3 class="font-bold text-lg mb-1">${grant.title}</h3>
                        <p class="text-gray-600 mb-2">${grant.funder}</p>
                        <div class="flex items-center space-x-4 text-sm">
                            <span class="text-gray-700">${amount}</span>
                            <span class="text-gray-500">Due: ${deadline}</span>
                            ${grant.link ? `<a href="${grant.link}" target="_blank" class="text-pink-600 hover:underline">View →</a>` : ''}
                        </div>
                        <div class="mt-2">
                            <span class="source-badge">${grant.source_name || grant.sourceName || 'Unknown Source'}</span>
                            ${grant.tags ? grant.tags.map(tag => `<span class="ml-2 px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">${tag}</span>`).join('') : ''}
                        </div>
                    </div>
                    <button class="btn-primary ml-4" onclick="saveGrant('${grant.id}')">
                        Save
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Filter opportunities
function filterOpportunities() {
    const sourceFilter = document.getElementById('source-filter').value;
    
    if (sourceFilter) {
        const filtered = opportunities.filter(grant => 
            (grant.source_name || grant.sourceName || '').includes(sourceFilter)
        );
        displayFilteredOpportunities(filtered);
    } else {
        displayOpportunities();
    }
}

// Sort opportunities
function sortOpportunities() {
    const sortBy = document.getElementById('sort-filter').value;
    
    const sorted = [...opportunities].sort((a, b) => {
        switch (sortBy) {
            case 'deadline':
                if (!a.deadline && !b.deadline) return 0;
                if (!a.deadline) return 1;
                if (!b.deadline) return -1;
                return new Date(a.deadline) - new Date(b.deadline);
            case 'amount':
                return (b.amount_max || b.amount || 0) - (a.amount_max || a.amount || 0);
            case 'discovered':
            default:
                return new Date(b.discovered_at || b.created_at) - new Date(a.discovered_at || a.created_at);
        }
    });
    
    opportunities = sorted;
    displayOpportunities();
}

// Display filtered opportunities
function displayFilteredOpportunities(filtered) {
    const container = document.getElementById('opportunities-list');
    const count = document.getElementById('opportunity-count');
    
    count.textContent = `${filtered.length} opportunities`;
    
    if (filtered.length === 0) {
        container.innerHTML = `<div class="text-center py-8 text-gray-600">No opportunities match your filter.</div>`;
        return;
    }
    
    // Use same display logic
    const temp = opportunities;
    opportunities = filtered;
    displayOpportunities();
    opportunities = temp;
}

// Save grant to Saved Grants
async function saveGrant(grantId) {
    const grant = opportunities.find(g => g.id === grantId);
    if (!grant) return;
    
    try {
        const response = await fetch(`/api/grants/${grantId}/save`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess(`"${grant.title}" saved! View in Saved Grants.`);
            
            // Update button state to show it's saved
            const saveButton = event.target;
            if (saveButton) {
                saveButton.textContent = '✓ Saved';
                saveButton.disabled = true;
                saveButton.style.opacity = '0.6';
                saveButton.style.cursor = 'not-allowed';
            }
        } else {
            showError(data.message || data.error || 'Failed to save grant');
        }
    } catch (error) {
        console.error('Error saving grant:', error);
        showError('Failed to save grant. Please try again.');
    }
}

// Load watchlists
async function loadWatchlists() {
    try {
        let data;
        
        if (DATA_MODE === 'API') {
            const response = await fetch('/api/watchlists');
            data = await response.json();
        } else {
            // Mock data fallback
            data = {
                success: true,
                watchlists: getMockWatchlists()
            };
        }
        
        if (data.success) {
            watchlists = data.watchlists || [];
            displayWatchlists();
        }
    } catch (error) {
        console.error('Error loading watchlists:', error);
        watchlists = getMockWatchlists();
        displayWatchlists();
    }
}

// Display watchlists
function displayWatchlists() {
    const container = document.getElementById('watchlists-container');
    
    if (watchlists.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-8 text-gray-600">
                No watchlists created yet. Add a watchlist to monitor grants for specific cities.
            </div>
        `;
        return;
    }
    
    container.innerHTML = watchlists.map(watchlist => {
        const lastRun = watchlist.lastRun ? 
            `Last run: ${new Date(watchlist.lastRun).toLocaleDateString()}` : 
            'Never run';
        
        return `
            <div class="watchlist-card">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-lg font-bold">${watchlist.city}</h3>
                    <button class="text-gray-400 hover:text-gray-600" onclick="deleteWatchlist(${watchlist.id})">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <p class="text-sm text-gray-600 mb-4">${lastRun}</p>
                
                <div class="space-y-2 mb-4">
                    ${(watchlist.sources || []).map(source => `
                        <div class="flex items-center justify-between">
                            <span class="text-sm">${getSourceName(source)}</span>
                            <div class="source-toggle ${watchlist.enabled ? 'active' : ''}" 
                                 onclick="toggleSource('${watchlist.id}', '${source}', this)">
                                <div class="source-toggle-handle"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="flex space-x-2">
                    <button class="btn-primary flex-1" onclick="runWatchlist(${watchlist.id})">
                        Run Now
                    </button>
                    <button class="btn-secondary" onclick="editWatchlist(${watchlist.id})">
                        Edit
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Run all connectors
async function runAllConnectors() {
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Running...';
    
    try {
        let data;
        
        if (DATA_MODE === 'API') {
            const response = await fetch('/api/discovery/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            data = await response.json();
        } else {
            // Mock response
            data = {
                success: true,
                totalFetched: 15,
                newGrantsSaved: 12,
                duplicatesSkipped: 3
            };
        }
        
        if (data.success) {
            showSuccess(`Fetched ${data.totalFetched} grants. ${data.newGrantsSaved} new, ${data.duplicatesSkipped} duplicates skipped.`);
            loadOpportunities();
        } else {
            showError('Failed to run discovery connectors.');
        }
    } catch (error) {
        console.error('Error running connectors:', error);
        showError('Failed to run discovery connectors.');
    } finally {
        button.disabled = false;
        button.textContent = 'Run All Connectors';
    }
}

// Run specific watchlist
async function runWatchlist(watchlistId) {
    const watchlist = watchlists.find(w => w.id === watchlistId);
    if (!watchlist) return;
    
    try {
        let data;
        
        if (DATA_MODE === 'API') {
            const response = await fetch(`/api/watchlists/${watchlistId}/run`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            data = await response.json();
        } else {
            // Mock response
            data = {
                success: true,
                totalFetched: 5,
                newGrantsSaved: 3,
                duplicatesSkipped: 2
            };
        }
        
        if (data.success) {
            showSuccess(`${watchlist.city}: Fetched ${data.totalFetched} grants. ${data.newGrantsSaved} new.`);
            // Update last run time
            watchlist.lastRun = new Date().toISOString();
            displayWatchlists();
            loadOpportunities();
        }
    } catch (error) {
        console.error('Error running watchlist:', error);
        showError(`Failed to run watchlist for ${watchlist.city}.`);
    }
}

// Add new watchlist
function addWatchlist() {
    const city = prompt('Enter city name:');
    if (!city) return;
    
    // Create default watchlist
    const newWatchlist = {
        city: city,
        sources: ['grants_gov', 'federal_register'],
        enabled: true
    };
    
    if (DATA_MODE === 'API') {
        fetch('/api/watchlists', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(newWatchlist)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(`Watchlist for ${city} created.`);
                loadWatchlists();
            }
        })
        .catch(error => {
            console.error('Error creating watchlist:', error);
            showError('Failed to create watchlist.');
        });
    } else {
        // Mock add
        newWatchlist.id = Date.now();
        watchlists.push(newWatchlist);
        displayWatchlists();
        showSuccess(`Watchlist for ${city} created.`);
    }
}

// Delete watchlist
function deleteWatchlist(watchlistId) {
    if (!confirm('Are you sure you want to delete this watchlist?')) return;
    
    if (DATA_MODE === 'API') {
        fetch(`/api/watchlists/${watchlistId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('Watchlist deleted.');
                loadWatchlists();
            }
        })
        .catch(error => {
            console.error('Error deleting watchlist:', error);
            showError('Failed to delete watchlist.');
        });
    } else {
        // Mock delete
        watchlists = watchlists.filter(w => w.id !== watchlistId);
        displayWatchlists();
        showSuccess('Watchlist deleted.');
    }
}

// Edit watchlist
function editWatchlist(watchlistId) {
    // TODO: Open modal to edit sources
    alert('Edit functionality will be implemented with a proper modal.');
}

// Toggle source
function toggleSource(watchlistId, sourceId, element) {
    element.classList.toggle('active');
    // TODO: Update watchlist sources via API
}

// Get human-readable source name
function getSourceName(sourceId) {
    const sourceNames = {
        'grants_gov': 'Grants.gov',
        'federal_register': 'Federal Register',
        'philanthropy_news': 'Philanthropy News Digest',
        'gr_foundation_1': 'Grand Rapids Community Foundation',
        'gr_foundation_2': 'Steelcase Foundation',
        'gr_foundation_3': 'Frey Foundation',
        'gr_foundation_4': 'Wege Foundation',
        'gr_foundation_5': 'DeVos Family Foundation'
    };
    return sourceNames[sourceId] || sourceId;
}

// Mock data functions
function getMockOpportunities() {
    return [
        {
            id: 'opp-1',
            title: 'Community Development Block Grant',
            funder: 'Department of Housing and Urban Development',
            amount_min: 50000,
            amount_max: 500000,
            deadline: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000).toISOString(),
            link: 'https://grants.gov/opportunity/12345',
            source_name: 'Grants.gov',
            tags: ['Community Development', 'Housing'],
            discovered_at: new Date().toISOString()
        },
        {
            id: 'opp-2',
            title: 'Arts Innovation Grant',
            funder: 'National Arts Foundation',
            amount_max: 50000,
            deadline: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            source_name: 'Philanthropy News Digest',
            tags: ['Arts', 'Culture'],
            discovered_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: 'opp-3',
            title: 'Grand Rapids Community Impact Grant',
            funder: 'Grand Rapids Community Foundation',
            amount_min: 5000,
            amount_max: 25000,
            deadline: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
            source_name: 'Grand Rapids Community Foundation',
            tags: ['Local', 'Community'],
            discovered_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
        }
    ];
}

function getMockWatchlists() {
    return [
        {
            id: 1,
            city: 'Grand Rapids',
            sources: ['gr_foundation_1', 'gr_foundation_2', 'gr_foundation_3', 'gr_foundation_4', 'gr_foundation_5'],
            enabled: true,
            lastRun: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: 2,
            city: 'Charlotte',
            sources: ['grants_gov', 'federal_register'],
            enabled: true,
            lastRun: null
        },
        {
            id: 3,
            city: 'Atlanta',
            sources: ['grants_gov', 'federal_register', 'philanthropy_news'],
            enabled: true,
            lastRun: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
        }
    ];
}

// Utility functions
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

function showSuccess(message) {
    // TODO: Implement toast notification
    console.log('Success:', message);
    alert(message);
}

function showError(message) {
    // TODO: Implement toast notification
    console.error('Error:', message);
    alert('Error: ' + message);
}
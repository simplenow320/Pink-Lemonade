// CRM Dashboard JavaScript
let dashboardData = {
    metrics: {},
    recentActivity: [],
    watchlists: [],
    grants: []
};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    loadOrganizationInfo();
    setInterval(refreshActivity, 30000); // Refresh activity every 30 seconds
});

// Load all dashboard data
async function loadDashboardData() {
    try {
        // Load all data in parallel for better performance
        const [metricsData, activityData, watchlistsData, grantsData] = await Promise.all([
            fetchMetrics(),
            fetchRecentActivity(),
            fetchWatchlists(),
            fetchUpcomingGrants()
        ]);
        
        // Update UI with loaded data
        updateMetrics(metricsData);
        updateActivityFeed(activityData);
        updateWatchlistOverview(watchlistsData);
        updateGrantsSnapshot(grantsData);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        // Use fallback mock data if API fails
        loadMockData();
    }
}

// Fetch metrics from API
async function fetchMetrics() {
    try {
        const response = await fetch('/api/dashboard/metrics');
        const data = await response.json();
        if (data.success) {
            dashboardData.metrics = data.metrics;
            return data.metrics;
        }
    } catch (error) {
        console.error('Error fetching metrics:', error);
    }
    return getMockMetrics();
}

// Fetch recent activity from API
async function fetchRecentActivity() {
    try {
        const response = await fetch('/api/dashboard/recent-activity');
        const data = await response.json();
        if (data.success) {
            dashboardData.recentActivity = data.activities;
            return data.activities;
        }
    } catch (error) {
        console.error('Error fetching activity:', error);
    }
    return getMockActivity();
}

// Fetch watchlists
async function fetchWatchlists() {
    try {
        const response = await fetch('/api/watchlists');
        const data = await response.json();
        if (data.success) {
            dashboardData.watchlists = data.watchlists;
            return data.watchlists;
        }
    } catch (error) {
        console.error('Error fetching watchlists:', error);
    }
    return getMockWatchlists();
}

// Fetch upcoming grants
async function fetchUpcomingGrants() {
    try {
        const response = await fetch('/api/grants?sort=deadline&limit=5');
        const data = await response.json();
        if (data.success) {
            dashboardData.grants = data.grants;
            return data.grants;
        }
    } catch (error) {
        console.error('Error fetching grants:', error);
    }
    return getMockGrants();
}

// Load organization info
async function loadOrganizationInfo() {
    try {
        const response = await fetch('/api/organization');
        const data = await response.json();
        if (data.success && data.organization) {
            document.getElementById('org-name').textContent = data.organization.name || 'Your Organization';
            document.getElementById('user-name').textContent = `Welcome, ${data.organization.name || 'User'}`;
            
            // Load custom logo if available
            if (data.organization.logo_url) {
                const logo = document.getElementById('org-logo');
                logo.src = data.organization.logo_url;
                logo.style.display = 'block';
                document.getElementById('fallback-logo').style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error loading organization info:', error);
    }
}

// Update metrics display
function updateMetrics(metrics) {
    // Total Grants
    const totalGrants = metrics.totalGrants || 0;
    document.getElementById('total-grants').textContent = totalGrants;
    
    // Funds Applied For
    const fundsApplied = metrics.fundsApplied || 0;
    document.getElementById('funds-applied').textContent = formatCurrency(fundsApplied);
    
    // Funds Won
    const fundsWon = metrics.fundsWon || 0;
    document.getElementById('funds-won').textContent = formatCurrency(fundsWon);
    
    // Win Rate
    const winRate = metrics.winRate || 0;
    document.getElementById('win-rate').textContent = `${Math.round(winRate)}%`;
}

// Update activity feed
function updateActivityFeed(activities) {
    const feedContainer = document.getElementById('activity-feed');
    
    if (!activities || activities.length === 0) {
        feedContainer.innerHTML = `
            <div class="text-center py-4 text-gray-500">
                No recent activity
            </div>
        `;
        return;
    }
    
    feedContainer.innerHTML = activities.slice(0, 5).map(activity => {
        const timeAgo = getTimeAgo(activity.timestamp);
        const icon = getActivityIcon(activity.type);
        
        return `
            <div class="activity-item">
                <div class="flex items-start">
                    <div class="mr-3 mt-1">${icon}</div>
                    <div class="flex-1">
                        <p class="text-sm text-gray-900">${activity.description}</p>
                        <p class="text-xs text-gray-500 mt-1">${timeAgo}</p>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Update watchlist overview
function updateWatchlistOverview(watchlists) {
    const container = document.getElementById('watchlist-overview');
    
    if (!watchlists || watchlists.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-gray-500">
                No watchlists configured
                <a href="/discovery#watchlists" class="block mt-2 text-pink-600 hover:underline">
                    Create your first watchlist →
                </a>
            </div>
        `;
        return;
    }
    
    container.innerHTML = watchlists.map(watchlist => {
        const newCount = watchlist.newOpportunities || 0;
        return `
            <div class="watchlist-item">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="font-medium text-gray-900">${watchlist.city}</p>
                        <p class="text-xs text-gray-500">${watchlist.sources?.length || 0} sources</p>
                    </div>
                    ${newCount > 0 ? `<span class="new-badge">${newCount} new</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Update grants snapshot table
function updateGrantsSnapshot(grants) {
    const tbody = document.getElementById('grants-snapshot');
    
    if (!grants || grants.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4 text-gray-500">
                    No upcoming deadlines
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = grants.slice(0, 5).map(grant => {
        const amount = grant.amount ? formatCurrency(grant.amount) : 
                      (grant.amount_max ? `Up to ${formatCurrency(grant.amount_max)}` : 'TBD');
        const deadline = grant.due_date ? formatDate(grant.due_date) : 
                        (grant.deadline ? formatDate(grant.deadline) : 'No deadline');
        const statusBadge = getStatusBadge(grant.status);
        
        return `
            <tr class="table-row cursor-pointer" onclick="viewGrant('${grant.id}')">
                <td class="py-3 px-3">
                    <p class="font-medium text-gray-900 text-sm">${truncateText(grant.title, 40)}</p>
                </td>
                <td class="py-3 px-3">
                    <p class="text-sm text-gray-600">${truncateText(grant.funder, 30)}</p>
                </td>
                <td class="py-3 px-3">
                    <p class="text-sm text-gray-900 font-medium">${amount}</p>
                </td>
                <td class="py-3 px-3">
                    ${statusBadge}
                </td>
                <td class="py-3 px-3">
                    <p class="text-sm text-gray-600">${deadline}</p>
                </td>
            </tr>
        `;
    }).join('');
}

// Filter grants by status
function filterGrantsByStatus(status) {
    // Navigate to grants page with status filter
    if (status === 'all') {
        window.location.href = '/grants';
    } else if (status === 'applied') {
        window.location.href = '/grants?status=submitted';
    } else if (status === 'won') {
        window.location.href = '/grants?status=won';
    }
}

// Show win rate details
function showWinRateDetails() {
    // Navigate to analytics page
    window.location.href = '/analytics';
}

// View specific grant
function viewGrant(grantId) {
    window.location.href = `/grants#grant-${grantId}`;
}

// Refresh activity feed
async function refreshActivity() {
    const activityData = await fetchRecentActivity();
    updateActivityFeed(activityData);
}

// Utility Functions
function formatCurrency(amount) {
    if (!amount) return '$0';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function formatDate(dateString) {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.ceil((date - now) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'Past due';
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays <= 7) return `${diffDays} days`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function getTimeAgo(timestamp) {
    if (!timestamp) return 'Just now';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
}

function getActivityIcon(type) {
    const icons = {
        'grant_added': '➕',
        'grant_updated': '✏️',
        'deadline_approaching': '⏰',
        'status_changed': '🔄',
        'note_added': '💬',
        'watchlist_alert': '🔔'
    };
    return icons[type] || '📌';
}

function getStatusBadge(status) {
    const statusClasses = {
        'idea': 'status-idea',
        'researching': 'status-researching',
        'writing': 'status-writing',
        'submitted': 'status-submitted',
        'won': 'status-won',
        'declined': 'status-declined'
    };
    
    const statusText = {
        'idea': 'Idea',
        'researching': 'Researching',
        'writing': 'Writing',
        'submitted': 'Submitted',
        'won': 'Won',
        'declined': 'Declined'
    };
    
    const className = statusClasses[status?.toLowerCase()] || 'status-idea';
    const text = statusText[status?.toLowerCase()] || status || 'Unknown';
    
    return `<span class="status-badge ${className}">${text}</span>`;
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function logout() {
    // Implement logout functionality
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}

// Mock Data Functions
function getMockMetrics() {
    return {
        totalGrants: 12,
        fundsApplied: 875000,
        fundsWon: 125000,
        winRate: 33
    };
}

function getMockActivity() {
    return [
        {
            type: 'grant_added',
            description: 'New grant added: Community Development Block Grant',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
        },
        {
            type: 'deadline_approaching',
            description: 'Deadline in 3 days: Youth Mentoring Program Grant',
            timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString()
        },
        {
            type: 'status_changed',
            description: 'Status updated to "Submitted" for Arts Innovation Grant',
            timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
        },
        {
            type: 'watchlist_alert',
            description: '5 new opportunities found in Grand Rapids watchlist',
            timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            type: 'note_added',
            description: 'Note added to Education Technology Grant',
            timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
        }
    ];
}

function getMockWatchlists() {
    return [
        {
            city: 'Grand Rapids',
            sources: ['gr_foundation_1', 'gr_foundation_2', 'gr_foundation_3'],
            newOpportunities: 3
        },
        {
            city: 'Charlotte',
            sources: ['grants_gov', 'federal_register'],
            newOpportunities: 0
        },
        {
            city: 'Atlanta',
            sources: ['grants_gov', 'philanthropy_news'],
            newOpportunities: 2
        }
    ];
}

function getMockGrants() {
    return [
        {
            id: '1',
            title: 'Community Development Block Grant',
            funder: 'Department of Housing and Urban Development',
            amount_max: 500000,
            status: 'writing',
            due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: '2',
            title: 'Youth Mentoring Program Grant',
            funder: 'National Youth Foundation',
            amount: 75000,
            status: 'researching',
            due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: '3',
            title: 'Arts Innovation Grant',
            funder: 'State Arts Council',
            amount_max: 50000,
            status: 'submitted',
            due_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: '4',
            title: 'Technology Infrastructure Grant',
            funder: 'Tech Foundation',
            amount: 100000,
            status: 'idea',
            due_date: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: '5',
            title: 'Community Health Initiative',
            funder: 'Health Foundation',
            amount_max: 250000,
            status: 'writing',
            due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
        }
    ];
}

// Load mock data as fallback
function loadMockData() {
    updateMetrics(getMockMetrics());
    updateActivityFeed(getMockActivity());
    updateWatchlistOverview(getMockWatchlists());
    updateGrantsSnapshot(getMockGrants());
}
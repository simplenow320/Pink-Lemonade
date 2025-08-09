# Fundraising CRM Dashboard Documentation

## Overview
The Fundraising CRM Dashboard is the main landing page after login, providing a centralized hub for grant tracking, key performance indicators (KPIs), and quick actions. It features a minimalist, clean, modern muted matte design aesthetic.

## Sections

### 1. Hero / Welcome Section
- **Logo Placement**: Prominently displayed in the center-left of the hero area (and ONLY here)
- **Organization Greeting**: Personalized welcome with organization name from user profile
- **Subtitle**: "Your fundraising command center — track, discover, and win grants."
- **Quick Actions**:
  - "Add New Grant" button → Links to grant creation form
  - "View Opportunities" button → Links to Discovery page

### 2. Key Metrics Row
Four interactive metric cards displaying:
- **Total Grants in Pipeline**: Count of all grants in the system
- **Total Funds Applied For**: Sum of amounts for submitted/won/declined grants
- **Total Funds Won**: Sum of amounts for grants with "won" status
- **Win Rate %**: Percentage of won grants among decided grants (won + declined)

Each card is clickable and filters the Grants table by relevant status.

### 3. Recent Activity Feed
Scrollable list showing the 5 most recent activities:
- Grant additions and updates
- Approaching deadlines
- Status changes
- Notes and comments
- Watchlist alerts

Each item includes timestamp and activity icon.

### 4. Watchlist Overview
Compact panel showing:
- List of current city-based watchlists
- Number of new opportunities found since last check
- "Manage Watchlists" link to full watchlist management

### 5. Saved Grants Snapshot
Table preview of top 5 grants sorted by nearest deadline:
- **Columns**: Title, Funder, Amount, Status, Deadline
- **Features**: Clickable rows for detailed view
- **"View All" button**: Links to full Saved Grants page

## API Endpoints

### `/api/dashboard/metrics`
Returns KPI data including:
```json
{
  "totalGrants": 12,
  "fundsApplied": 875000,
  "fundsWon": 125000,
  "winRate": 33,
  "activeGrants": 8,
  "upcomingDeadlines": 3
}
```

### `/api/dashboard/recent-activity`
Returns latest activity items:
```json
{
  "activities": [
    {
      "type": "grant_added",
      "description": "New grant added: Community Development Block Grant",
      "timestamp": "2025-08-09T10:30:00Z",
      "grantId": "grant-123"
    }
  ]
}
```

### `/api/dashboard/summary`
Returns complete dashboard data in one call (for optimization).

## KPI Calculation Logic

### Total Grants in Pipeline
- **Query**: `SELECT COUNT(*) FROM grants WHERE org_id = :org_id`
- **Description**: All grants regardless of status

### Total Funds Applied For
- **Query**: `SELECT SUM(COALESCE(amount, amount_max)) FROM grants WHERE org_id = :org_id AND status IN ('submitted', 'won', 'declined')`
- **Description**: Sum of grant amounts where applications have been submitted

### Total Funds Won
- **Query**: `SELECT SUM(COALESCE(amount, amount_max)) FROM grants WHERE org_id = :org_id AND status = 'won'`
- **Description**: Sum of grant amounts with "won" status

### Win Rate
- **Calculation**: `(won_count / (won_count + declined_count)) * 100`
- **Description**: Percentage of successful grants among decided applications

## Customization

### Adjusting Dashboard Layout
1. Edit `app/templates/crm-dashboard.html` for structural changes
2. Modify grid classes for responsive breakpoints
3. Update section ordering by moving div blocks

### Modifying KPI Logic
1. Edit `app/api/dashboard.py` in the `get_dashboard_metrics()` function
2. Update SQL queries or calculation logic
3. Add new metrics to the response object

### Styling Changes
1. Edit CSS variables in `crm-dashboard.html` `<style>` section
2. Maintain Pink Lemonade brand colors:
   - Pink: #ec4899
   - Pink Light: #f9a8d4
   - Pink Dark: #be185d
   - Matte Pink: #e8a5c0
   - Matte Grey: #9ca3af

### Cache Management
- Metrics are cached in session for performance
- Clear cache via `/api/dashboard/cache/clear` endpoint
- Auto-refresh occurs every 30 seconds for activity feed

## Files Modified/Added

### New Files Created:
- `app/templates/crm-dashboard.html` - Main dashboard template
- `app/static/js/crm-dashboard.js` - Dashboard JavaScript functionality
- `app/api/dashboard.py` - Dashboard API endpoints
- `web/docs/dashboard.md` - This documentation file

### Modified Files:
- `app/__init__.py` - Added dashboard blueprint registration
- `app/routes.py` - Updated dashboard route to use new template
- `app/db_migrations/add_discovery_fields_to_grants.py` - Added discovery fields migration

## Performance Optimizations
1. **Parallel Data Loading**: All dashboard sections load simultaneously
2. **Mock Data Fallback**: Displays sample data if API fails
3. **Session Caching**: Metrics cached to reduce database queries
4. **Auto-refresh**: Activity feed updates every 30 seconds

## Mobile/Tablet Responsiveness
- Hero section stacks vertically on mobile
- Metric cards display in single column on small screens
- Activity feed and watchlists stack above grants table on tablets
- All tables are horizontally scrollable on mobile

## Testing Checklist
✓ Dashboard loads with both mock and live data
✓ Metrics accurately reflect underlying grant data
✓ Activity feed updates in real-time or on refresh
✓ Logo appears only in hero section
✓ All navigation links function correctly
✓ Metric cards filter grants when clicked
✓ Dashboard responsive on all screen sizes
✓ No null values displayed in KPI cards
✓ Minimalist matte aesthetic consistently applied
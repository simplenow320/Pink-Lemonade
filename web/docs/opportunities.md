# Opportunities Page Documentation

## Overview
The Opportunities page provides a unified interface for discovering and managing grant opportunities from multiple live data sources through the API Manager.

## Features

### Data Sources
- **Live Sources**: Grants.gov, Federal Register, GovInfo, Philanthropy News Digest, Michigan Portal, Georgia Portal
- **Mock Mode**: Demo data for testing when API keys are not available
- **Mode Indicator**: DEMO badge displayed when in mock mode

### Search & Filtering
- **Text Search**: Full-text search across title, description, and funder
- **City Filter**: Filter by location (Atlanta, National, Georgia, Southeast)
- **Focus Area Filter**: Filter by program area (Youth, Education, Community, Faith, Health)
- **Deadline Filter**: Filter by deadline window (7, 30, 60, 90 days)
- **Source Filter**: Filter by specific data source

### Display Columns
1. **Title**: Grant opportunity name
2. **Funder**: Organization offering the grant
3. **Fit Score**: AI-powered match score (1-5) with organization profile
4. **Amount**: Funding range (min-max)
5. **Deadline**: Application due date
6. **Source**: Data source badge
7. **Actions**: Save and Apply buttons

### Actions
- **Save**: Moves opportunity to Saved Grants (org-scoped)
- **Apply**: Creates draft application with status=drafting

## Technical Implementation

### Frontend (opportunities.html)
- Mobile-first responsive design
- Branding: Matte pink (#db2777), white, grey, black only
- Real-time search and filtering
- Pagination for large result sets
- Clear empty states with guidance

### Backend API (opportunities.py)
- `/api/opportunities`: Main endpoint for fetching opportunities
  - Query parameters: page, search, city, focus_area, deadline_days, source
  - Returns paginated results with fit scores
- `/api/opportunities/save`: Save opportunity as grant
- `/api/opportunities/apply`: Create draft application

### API Manager Integration
All data fetches go through the centralized API Manager which:
- Handles live vs mock mode switching
- Manages API rate limits
- Provides fallback data when APIs are unavailable
- Caches responses for performance

### Organization Scoping
- All save/apply actions are scoped to the current organization
- Fit scores calculated based on organization profile
- Saved grants linked to org_id

## User Experience

### Empty States
- **No Results**: Clear message with filter reset option
- **API Unavailable**: Fallback to mock data with DEMO badge
- **No API Key**: Prompt to add keys in Settings

### Mobile Responsiveness
- Stacked layout on mobile devices
- Touch-friendly action buttons
- Collapsible filters
- Swipeable rows

### Performance
- Lazy loading of results
- Client-side filter caching
- Debounced search input
- Optimized pagination

## Testing Checklist

### Functional Tests
- [ ] Search returns relevant results
- [ ] All filters work independently and together
- [ ] Save action creates grant in Saved Grants
- [ ] Apply action creates draft in My Applications
- [ ] Pagination works correctly
- [ ] Filter state retained on navigation

### Display Tests
- [ ] DEMO badge shows in mock mode only
- [ ] Fit scores display correctly (1-5 or N/A)
- [ ] Empty states show appropriate guidance
- [ ] Source badges display correctly
- [ ] Mobile layout works on small screens

### Data Integrity
- [ ] No fake numbers in LIVE mode
- [ ] Organization scoping enforced
- [ ] Deadlines calculated correctly
- [ ] Amount ranges parsed properly
- [ ] Links to original sources work

## Debugging Guide

### Common Issues
1. **No opportunities loading**: Check API Manager configuration and API keys
2. **Filters not working**: Verify query parameter handling in backend
3. **Save/Apply failing**: Check organization exists and database connection
4. **Fit scores not showing**: Verify AI service is enabled with API key
5. **DEMO badge always showing**: Check data mode in API Manager

### Error Messages
- "Failed to load opportunities": API connection issue
- "Organization not found": No organization profile created
- "Failed to save": Database write error
- "Failed to add to applications": Grant creation error

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: For AI fit scoring
- `DATA_MODE`: Set to 'live' or 'mock'

### API Rate Limits
- Grants.gov: 100 calls/hour
- Federal Register: 1000 calls/hour
- GovInfo: 1000 calls/hour
- Philanthropy News: No official limit

## Future Enhancements
- Advanced filtering (custom date ranges, amount ranges)
- Saved searches with notifications
- Bulk operations (save/apply multiple)
- Export to CSV/PDF
- Calendar integration for deadlines
- Email alerts for new matches
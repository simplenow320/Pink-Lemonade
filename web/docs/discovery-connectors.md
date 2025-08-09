# Discovery Connectors Documentation

## Overview
The Discovery Connectors system is a comprehensive grant discovery platform that automatically pulls grant opportunities from multiple sources, manages city-based watchlists, and integrates discovered grants with the existing grants management system.

## Architecture

### Backend Components

#### 1. Discovery Service (`app/services/discovery.py`)
Core service managing all discovery connectors with the following capabilities:
- **Base Connector Class**: Abstract connector for standardized grant fetching
- **Specialized Connectors**: 
  - GrantsGovConnector (Federal grants)
  - FederalRegisterConnector (Federal notices)
  - PhilanthropyNewsConnector (Foundation RFPs)
  - CityFoundationConnector (Local foundation grants)
- **Deduplication Logic**: Prevents duplicate grants based on title+funder+deadline
- **Mock Data Fallback**: Returns sample data when APIs unavailable

#### 2. Watchlist Model (`app/models/watchlist.py`)
Database model for city-based grant monitoring:
- Tracks sources per city
- Enable/disable functionality
- Last run timestamps
- Default watchlists for major cities

#### 3. Discovery API (`app/api/discovery.py`)
RESTful endpoints for discovery operations:
- `POST /api/discovery/run` - Run all or specific connectors
- `GET /api/discovery/latest` - Fetch recently discovered grants
- `GET/POST/PUT/DELETE /api/watchlists` - CRUD operations for watchlists
- `POST /api/watchlists/{id}/run` - Run specific watchlist connectors

### Frontend Components

#### 1. Discovery Page (`app/templates/discovery.html`)
Main UI with two tabs:
- **Latest Opportunities**: Table view of discovered grants with filters
- **Watchlists**: City-based watchlist management

#### 2. Discovery JavaScript (`app/static/js/discovery.js`)
Client-side logic for:
- Opportunity display and filtering
- Watchlist management
- API/Mock data toggle
- Save grant functionality

## Adding New Connectors

### Step 1: Create Connector Class
```python
class MyNewConnector(DiscoveryConnector):
    def fetch(self):
        # Implement data fetching logic
        # Return list of grant dictionaries
        pass
    
    def parse(self, data):
        # Parse raw data into GrantRecord format
        pass
    
    def _fetch_mock(self):
        # Return mock data when API unavailable
        pass
```

### Step 2: Register in Discovery Service
```python
# In DiscoveryService._initialize_connectors()
connectors['my_connector'] = MyNewConnector({
    'id': 'my_connector',
    'name': 'My Connector Name',
    'type': 'api',  # or 'scrape'
    'endpoint': 'https://api.example.com/grants',
    'auth': {'api_key': 'YOUR_KEY'},
    'params': {},
    'source_url': 'https://example.com'
})
```

## Setting Up City Watchlists

### Default Watchlists
The system automatically creates watchlists for:
- Grand Rapids (5 local foundations)
- Charlotte (Federal sources)
- Atlanta (Federal sources)
- Detroit (Federal sources)
- Indiana (Federal + Philanthropy sources)

### Adding New City Watchlist

#### Via API:
```bash
curl -X POST http://localhost:5000/api/watchlists \
  -H "Content-Type: application/json" \
  -d '{
    "city": "San Francisco",
    "sources": ["grants_gov", "sf_foundation_1"],
    "enabled": true
  }'
```

#### Via UI:
1. Navigate to Discovery → Watchlists tab
2. Click "Add Watchlist"
3. Enter city name
4. Select relevant sources
5. Click "Save"

## Data Flow

### Discovery Process
1. User triggers discovery (manual or scheduled)
2. Connectors fetch data from sources
3. Raw data parsed into standardized GrantRecord format
4. Deduplication against existing grants
5. New grants saved with 'discovered' status
6. Grants appear in Latest Opportunities

### Watchlist Process
1. User creates/edits watchlist for specific city
2. Selects relevant connectors (local foundations, federal, etc.)
3. Runs watchlist to fetch targeted grants
4. Results filtered and deduplicated
5. New grants saved to database

## Switching Between API and Mock Mode

### For Backend Testing:
```python
# In app/services/discovery.py
# Change connector initialization:
'endpoint': 'MOCK'  # Use mock data
# or
'endpoint': 'https://actual-api.com'  # Use real API
```

### For Frontend Testing:
```javascript
// In app/static/js/discovery.js
let DATA_MODE = 'MOCK';  // Use mock data
// or
let DATA_MODE = 'API';   // Use backend API
```

## Grant Record Schema
All connectors must return grants in this format:
```json
{
  "title": "Grant Title",
  "funder": "Funding Organization",
  "link": "https://grant-url.com",
  "amountMin": 10000,
  "amountMax": 50000,
  "deadline": "2025-03-15T00:00:00",
  "geography": "National|Regional|State|Local",
  "eligibility": "Eligibility requirements text",
  "tags": ["Category1", "Category2"],
  "sourceName": "Grants.gov",
  "sourceURL": "https://grants.gov"
}
```

## Scheduling Automated Discovery

### Daily Discovery Job
```python
# In app/utils/scheduler.py
def schedule_discovery():
    schedule.every().day.at("00:00").do(run_all_discovery)
    
def run_all_discovery():
    from app.services.discovery import discovery_service
    grants = discovery_service.run_all_connectors()
    # Process and save grants
```

### Per-Watchlist Scheduling
```python
def schedule_watchlist(watchlist_id, frequency='daily'):
    if frequency == 'daily':
        schedule.every().day.do(run_watchlist, watchlist_id)
    elif frequency == 'weekly':
        schedule.every().week.do(run_watchlist, watchlist_id)
```

## Mock Data Sources

### Available Mock Connectors:
1. **Grants.gov**: Federal grants (2 samples)
2. **Federal Register**: Federal notices (1 sample)
3. **Philanthropy News**: Foundation RFPs (1 sample)
4. **Grand Rapids Foundations**: 5 local foundation grants

### Mock Data Location:
- Backend: Generated in each connector's `_fetch_mock()` method
- Frontend: `getMockOpportunities()` and `getMockWatchlists()` functions

## Testing Checklist

### Manual Testing:
✅ Run all connectors via UI button
✅ View latest opportunities with source filtering
✅ Create new watchlist for a city
✅ Run specific watchlist
✅ Toggle source enable/disable
✅ Save grant from discovery to Saved Grants
✅ Delete watchlist
✅ Sort opportunities by date/amount/deadline

### API Testing:
```bash
# Run all connectors
curl -X POST http://localhost:5000/api/discovery/run

# Get latest opportunities
curl http://localhost:5000/api/discovery/latest

# Create watchlist
curl -X POST http://localhost:5000/api/watchlists \
  -H "Content-Type: application/json" \
  -d '{"city": "Boston", "sources": ["grants_gov"]}'

# Run specific watchlist
curl -X POST http://localhost:5000/api/watchlists/1/run
```

## Troubleshooting

### Common Issues:

1. **No grants appearing**: Check DATA_MODE setting, verify connectors enabled
2. **Duplicate grants**: Verify deduplication logic working correctly
3. **API failures**: Check API keys in environment variables
4. **CORS errors**: Ensure Flask-CORS configured properly
5. **Database errors**: Run migrations, check Grant model fields

### Debug Mode:
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Advanced Matching**: AI-powered grant matching based on organization profile
2. **Email Notifications**: Alert users when new matching grants discovered
3. **Custom Connectors**: UI for adding custom RSS/API sources
4. **Smart Scheduling**: Adaptive scheduling based on source update frequency
5. **Bulk Actions**: Save/dismiss multiple grants at once
6. **Analytics**: Track discovery success rates and source effectiveness
7. **Export**: Download discovered grants as CSV/Excel
8. **API Rate Limiting**: Implement proper rate limiting for external APIs

## Summary

The Discovery Connectors system provides a robust, extensible platform for automated grant discovery. With support for multiple data sources, city-based watchlists, and seamless integration with the existing grants management system, organizations can efficiently discover and track relevant funding opportunities. The system's modular architecture makes it easy to add new sources and customize discovery strategies per organization's needs.
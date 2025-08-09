# API & Data Integration Layer Documentation

## Overview
The API & Data Integration Layer provides a centralized system for managing all external grant data sources. This unified approach makes it easy to add new APIs, manage rate limits, handle caching, and standardize data formats across multiple sources.

## Architecture

### Core Components

1. **API Manager** (`/app/services/apiManager.py`)
   - Central service handling all API calls
   - Rate limiting and caching
   - Data standardization
   - Error handling with fallback to mock data

2. **API Configuration** (`/app/config/apiConfig.py`)
   - Source definitions and settings
   - API keys and authentication
   - Rate limits and cache TTL
   - Field mapping configurations

3. **Integration API** (`/app/api/integration.py`)
   - RESTful endpoints for frontend
   - Source management
   - Data import capabilities
   - Testing and configuration

## Supported Data Sources

### Currently Enabled
- **Grants.gov** - Federal grant opportunities (Public API, no key required)
- **Philanthropy News Digest** - Foundation RFPs via RSS
- **Michigan Open Data Portal** - State grants
- **Georgia Grants Portal** - State funding

### Ready for Integration (Disabled by Default)
- **Foundation Directory Online** - Requires paid subscription
- **GrantWatch** - Requires API key
- **Candid** - Premium foundation data
- **North Carolina Grants**
- **South Carolina Grants**

## API Endpoints

### Source Management
```
GET /api/integration/sources
Returns list of all available data sources and their status
```

### Grant Search
```
POST /api/integration/search
{
  "query": "youth programs",
  "filters": {
    "category": "Education",
    "amount_min": 10000
  },
  "sources": ["grants_gov", "philanthropy_news"]  // Optional
}
```

### Fetch from Specific Source
```
GET /api/integration/fetch/<source_name>?limit=25&query=education
```

### Grant Details
```
GET /api/integration/grant/<grant_id>?source=grants_gov
```

### Import Grants to Database
```
POST /api/integration/import
{
  "grants": [
    {
      "title": "Grant Title",
      "funder": "Foundation Name",
      "amount_min": 10000,
      "amount_max": 50000,
      "deadline": "2024-12-31",
      "description": "Grant description",
      "source": "grants_gov"
    }
  ]
}
```

### Configure Source
```
POST /api/integration/configure
{
  "source_id": "grantwatch",
  "enabled": true,
  "api_key": "your-api-key-here"
}
```

### Test Connection
```
GET /api/integration/test/<source_name>
```

## Adding New Data Sources

### Step 1: Add Source Configuration
Edit `/app/config/apiConfig.py` and add your source:

```python
API_SOURCES = {
    'your_new_source': {
        'name': 'Your Source Name',
        'enabled': False,  # Set to True when ready
        'base_url': 'https://api.yoursource.com',
        'api_key': os.environ.get('YOUR_SOURCE_API_KEY'),
        'rate_limit': {
            'calls': 100,
            'period': 3600  # seconds
        },
        'cache_ttl': 60,  # minutes
        'supports': ['search', 'details'],
        'description': 'Description of your source'
    }
}
```

### Step 2: Implement Fetcher Method
Add a fetcher method in `/app/services/apiManager.py`:

```python
def _fetch_your_source(self, params: Dict) -> List[Dict]:
    """
    Fetch grants from Your Source
    """
    try:
        base_url = self.sources['your_new_source']['base_url']
        api_key = self.sources['your_new_source']['api_key']
        
        # Make API call
        response = requests.get(
            f"{base_url}/grants",
            headers={'Authorization': f'Bearer {api_key}'},
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            grants = []
            
            for item in data['results']:
                grant = self._standardize_grant({
                    'title': item.get('title'),
                    'funder': item.get('funder'),
                    'amount_min': item.get('min_amount'),
                    'amount_max': item.get('max_amount'),
                    'deadline': item.get('deadline'),
                    'description': item.get('description'),
                    'link': item.get('url'),
                    'source': 'Your Source Name',
                    'source_id': item.get('id')
                })
                grants.append(grant)
            
            return grants
            
    except Exception as e:
        logger.error(f"Error fetching from Your Source: {e}")
    
    return []
```

### Step 3: Add to Router
Update the router in `get_grants_from_source()` method:

```python
elif source_name == 'your_new_source':
    grants = self._fetch_your_source(params)
```

### Step 4: Set API Key
Add the API key to Replit Secrets:
- Key: `YOUR_SOURCE_API_KEY`
- Value: Your actual API key

### Step 5: Enable and Test
```bash
# Test the connection
curl http://localhost:5000/api/integration/test/your_new_source

# Enable the source
curl -X POST http://localhost:5000/api/integration/configure \
  -H "Content-Type: application/json" \
  -d '{"source_id": "your_new_source", "enabled": true}'

# Fetch data
curl http://localhost:5000/api/integration/fetch/your_new_source?limit=10
```

## Data Standardization

All grants are standardized to this format:

```json
{
  "id": "unique-grant-id",
  "title": "Grant Title",
  "funder": "Foundation Name",
  "amount_min": 10000,
  "amount_max": 50000,
  "deadline": "2024-12-31T00:00:00",
  "description": "Grant description",
  "eligibility": "Eligibility requirements",
  "link": "https://grant-application-url.com",
  "source": "Source Name",
  "source_url": "https://source-website.com",
  "tags": ["education", "youth"],
  "discovered_at": "2024-01-15T10:00:00",
  "status": "discovered"
}
```

## Rate Limiting

Each source has configurable rate limits:
- `calls`: Maximum number of API calls
- `period`: Time period in seconds

The API Manager automatically enforces these limits and returns cached or mock data when limits are exceeded.

## Caching

- Each source has a `cache_ttl` (Time To Live) in minutes
- Cached responses are automatically returned for repeated requests within the TTL
- Cache is invalidated after TTL expires

## Error Handling

The API Manager handles errors gracefully:
1. First attempts to fetch from the actual API
2. Falls back to cached data if available
3. Returns mock data if both fail
4. Logs all errors for debugging

## Integration with Existing Systems

### Dashboard
The Dashboard can pull metrics from the API Manager:
```python
from app.services.apiManager import api_manager

# Get recent grants from all sources
grants = api_manager.search_opportunities("", {"limit": 10})
```

### Watchlists
Watchlists use the API Manager for updates:
```python
# Get new grants for a watchlist
updates = api_manager.get_watchlist_updates(watchlist_id, last_check)
```

### Discovery Page
The Discovery page shows all available sources and allows filtering:
```javascript
// Fetch available sources
fetch('/api/integration/sources')
  .then(response => response.json())
  .then(data => {
    // Display sources with enable/disable toggles
  });

// Search across selected sources
fetch('/api/integration/search', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: searchQuery,
    sources: selectedSources
  })
});
```

## Monitoring and Debugging

### Check Source Status
```bash
curl http://localhost:5000/api/integration/sources
```

### View Logs
```python
# Logs are written to the application log
tail -f app.log | grep apiManager
```

### Test Individual Sources
```bash
# Test each source individually
for source in grants_gov philanthropy_news michigan_portal georgia_portal; do
  echo "Testing $source..."
  curl http://localhost:5000/api/integration/test/$source
done
```

## Best Practices

1. **Always use the API Manager** for external data fetching
2. **Respect rate limits** - Don't bypass the rate limiter
3. **Handle errors gracefully** - Always have fallback behavior
4. **Standardize data** - Use the `_standardize_grant()` method
5. **Cache appropriately** - Set reasonable TTL values
6. **Log errors** - Use proper logging for debugging
7. **Test thoroughly** - Test both success and failure cases

## Future Enhancements

- [ ] Add webhook support for real-time updates
- [ ] Implement OAuth 2.0 for secure API authentication
- [ ] Add data quality scoring
- [ ] Implement automatic retry with exponential backoff
- [ ] Add support for GraphQL APIs
- [ ] Create admin UI for source configuration
- [ ] Add metrics and monitoring dashboard
- [ ] Implement data deduplication across sources
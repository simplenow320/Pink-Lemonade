# API Manager Documentation

## Overview

The API Manager is a centralized service that handles all external data source integrations for Pink Lemonade. It provides a unified interface for accessing grant opportunities from multiple sources with built-in rate limiting, caching, and error handling.

## Integrated Data Sources

### 1. Grants.gov
- **Status**: ✅ Live Integration
- **Endpoint**: `https://www.grants.gov/grantsws/rest/opportunities/search`
- **Rate Limit**: 100 calls/hour
- **Cache TTL**: 60 minutes
- **Parameters**:
  - `keyword`: Search term
  - `oppStatus`: 'open' for active opportunities
  - `rows`: Number of results (default: 25)

### 2. Federal Register
- **Status**: ✅ Live Integration
- **Endpoint**: `https://www.federalregister.gov/api/v1/documents.json`
- **Rate Limit**: 1000 calls/hour
- **Cache TTL**: 120 minutes
- **Parameters**:
  - `conditions[term]`: Search term (default: 'grant funding')
  - `conditions[type][]`: 'NOTICE'
  - `conditions[agencies][]`: Target agencies
  - `fields[]`: Required fields
  - `per_page`: Results per page (default: 20)
  - `order`: 'newest'

### 3. GovInfo API
- **Status**: ✅ Live Integration
- **Endpoint**: `https://api.govinfo.gov/search`
- **Rate Limit**: 1000 calls/hour
- **Cache TTL**: 120 minutes
- **Parameters**:
  - `query`: Search term
  - `collection`: 'FR' (Federal Register)
  - `format`: 'json'
  - `pageSize`: Results per page (default: 25)
  - `offsetMark`: Pagination marker

### 4. Philanthropy News Digest
- **Status**: ⚠️ Limited (feedparser dependency)
- **Endpoint**: `https://philanthropynewsdigest.org/rfps/rss`
- **Rate Limit**: 50 calls/hour
- **Cache TTL**: 120 minutes
- **Notes**: Falls back to mock data if feedparser not available

### 5. State Portals
- **Michigan Portal**: Mock data (placeholder for future integration)
- **Georgia Portal**: Mock data (placeholder for future integration)

## API Usage

### Search Across All Sources
```python
from app.services.apiManager import search_opportunities

grants = search_opportunities(
    query="youth programs",
    filters={
        'limit': 50,
        'category': 'Youth Programs'
    }
)
```

### Query Specific Source
```python
from app.services.apiManager import get_grants_from_source

grants = get_grants_from_source(
    'grants_gov',
    {'query': 'nonprofit', 'limit': 25}
)
```

## Data Standardization

All grant data is standardized to the following format:
```json
{
    "id": "unique_identifier",
    "title": "Grant Title",
    "funder": "Funding Organization",
    "amount_min": 10000,
    "amount_max": 50000,
    "deadline": "2024-12-31",
    "description": "Grant description",
    "eligibility": "Eligibility requirements",
    "link": "https://...",
    "source": "Source Name",
    "source_url": "https://...",
    "tags": ["tag1", "tag2"],
    "discovered_at": "2024-01-01T00:00:00",
    "status": "discovered"
}
```

## Configuration

### Environment Variables
- `APP_DATA_MODE`: Set to 'LIVE' or 'MOCK' to control data sources
- API keys (if needed) follow pattern: `{SOURCE}_API_KEY`

### Adding New Sources
1. Add configuration to `app/config/apiConfig.py`
2. Implement fetcher method in `app/services/apiManager.py`
3. Add routing logic in `get_grants_from_source()`
4. Update this documentation

## Rate Limiting & Caching

- Built-in rate limiting prevents API quota exhaustion
- Intelligent caching reduces redundant API calls
- Fallback to mock data when rate limits exceeded
- Cache keys based on source + parameters hash

## Error Handling

- Graceful degradation to mock data on API failures
- Comprehensive logging for debugging
- Timeout protection (10 seconds per request)
- Structured error responses

## Data Mode Behavior

### LIVE Mode (`APP_DATA_MODE=LIVE`)
- Real API calls to external sources
- Empty states when no data available
- N/A displayed for missing metrics
- LIVE badge shown in UI

### MOCK Mode (`APP_DATA_MODE=MOCK`)
- Demo data for development/testing
- Consistent placeholder content
- DEMO badge shown in UI
- Fallback when APIs unavailable

## Testing

Use the `/api-test` endpoint to verify API connectivity:
- Lists all configured sources
- Shows enabled/disabled status
- Tests live connections
- Displays sample data

## Endpoints

### Dashboard Integration
- `/api/dashboard/metrics` - Real grant metrics or N/A in LIVE mode
- `/api/grants` - Saved grants from database
- `/api/discovery/run` - Trigger discovery across all sources

### API Manager Endpoints
- `/api/sources` - List all configured sources
- `/api/search` - Search across sources with filters
- `/api/discovery/connectors` - Discovery connector status

## Future Enhancements

1. **Additional Sources**:
   - Foundation Directory Online (paid API)
   - GrantWatch (subscription required)
   - Candid/Foundation Center

2. **Advanced Features**:
   - Machine learning relevance scoring
   - Automatic grant categorization
   - Duplicate detection algorithms
   - Historical trend analysis

3. **Performance**:
   - Async request processing
   - Redis caching layer
   - Database indexing optimization
   - API response compression

## Troubleshooting

### Common Issues
1. **Rate Limits**: Check logs for "Rate limit exceeded" messages
2. **API Timeouts**: Verify network connectivity and endpoint availability
3. **Missing Data**: Confirm APP_DATA_MODE setting and source configuration
4. **Cache Issues**: Clear cache through `/api/dashboard/cache/clear`

### Debug Steps
1. Check `/api-test` for source status
2. Review application logs for error details
3. Verify environment variables
4. Test individual source endpoints
5. Monitor rate limit counters

Last Updated: August 9, 2025
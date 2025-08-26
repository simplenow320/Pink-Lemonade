# Grant Matching Implementation Checklist

## Planned Components

### Services Layer
- **candid_client.py** - Enhanced client with key rotation and caching for News/Grants APIs
- **essentials_client.py** - New client for Candid Essentials API (PCS codes, org lookup)  
- **matching_service.py** - Blends News + Grants + existing Grants.gov data for comprehensive matching

### API Layer  
- **/api/matching routes** - Endpoints for grant matching with multi-source data feeds

### Testing
- **unit tests** - Test clients, services, and API endpoints
- **smoke script** - End-to-end validation of matching flow

## Implementation Notes
- Use existing project structure (app/services, app/api, tests/)
- Maintain key rotation and caching patterns from existing candid_client.py
- Integrate with existing Grants.gov client if present
- No UI/layout changes - backend services only
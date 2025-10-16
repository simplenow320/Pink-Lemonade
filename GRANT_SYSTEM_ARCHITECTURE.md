# Grant Fetching & Scraping System Architecture

## Overview
The GrantFlow platform uses a sophisticated multi-source grant discovery system that fetches, scrapes, persists, and scores grant opportunities from numerous sources. The system is designed to handle millions of grant records efficiently with deduplication, AI scoring, and intelligent caching.

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Federal Sources           Foundation Sources    State/Local │
│  ├─ Grants.gov API        ├─ Candid API         ├─ Socrata  │
│  ├─ SAM.gov API           ├─ Foundation Sites   ├─ NY State │
│  ├─ Federal Register      └─ Custom Scrapers    └─ SF Portal│
│  ├─ USAspending.gov                                          │
│  ├─ HHS Grants                                               │
│  ├─ Education.gov                                            │
│  └─ NSF Awards                                               │
│                                                               │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              DATA COLLECTION LAYER                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  MatchingService          GrantFetcher      ScraperService  │
│  ├─ Orchestrates APIs     ├─ Bulk fetch    ├─ Web scraping │
│  ├─ Query builder         ├─ Multi-source  ├─ HTML parsing │
│  └─ Rate limiting         └─ Scheduling    └─ Data extract │
│                                                               │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│         GRANT DISCOVERY SERVICE V2 (Single Source of Truth)  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  discover_and_persist()                                      │
│  ├─ Check cache (24hr window)                               │
│  ├─ Fetch from all sources                                  │
│  ├─ Deduplicate by URL & title                              │
│  ├─ Persist to database                                     │
│  └─ Trigger AI scoring                                      │
│                                                               │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              DATABASE PERSISTENCE                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  PostgreSQL Grant Table                                      │
│  ├─ Core Fields: title, funder, deadline, amounts           │
│  ├─ Contact Fields: email, phone, contact_name              │
│  ├─ AI Fields: match_score, match_reason                    │
│  ├─ Tracking: source_name, source_url, created_at           │
│  └─ Status: discovery → writing → submitted → awarded       │
│                                                               │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              AI ENHANCEMENT LAYER                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  AIGrantMatcher           ContactExtractor    Intelligence  │
│  ├─ REACTO prompts       ├─ Email patterns   ├─ Summary gen │
│  ├─ Score 1-5            ├─ Phone extract    ├─ Requirement │
│  └─ Match reasoning      └─ Contact names    └─ Complexity  │
│                                                               │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              APPLICATION LAYER                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  API Endpoints            Smart Tools         Frontend       │
│  ├─ /api/matching/       ├─ Case Support    ├─ Discovery   │
│  ├─ /api/grants/         ├─ Impact Report   ├─ Pipeline    │
│  └─ /api/smart-tools/    └─ Narratives      └─ Analytics   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. **Data Sources (29M+ Grants)**

#### Federal Sources
- **Grants.gov**: 2,000+ active federal opportunities via GSA Search API
- **SAM.gov**: Federal contracts and assistance listings (API key required)
- **Federal Register**: Early grant notices and NOFOs
- **USAspending.gov**: Historical federal spending data
- **Agency-Specific**: HHS, Education.gov, NSF direct APIs

#### Foundation Sources
- **Candid API Suite**: 
  - News API: Foundation announcements
  - Grants API: 100,000+ foundation opportunities
  - Premium Database: Deep foundation intelligence
- **Foundation Websites**: 70+ foundations via custom scrapers
- **Corporate Giving**: Tech companies, AI funders

#### State/Local Sources
- **Socrata SODA API**: NY State and San Francisco portals
- **State Grant Portals**: Direct integration where available

### 2. **Data Collection Services**

#### MatchingService (`matching_service.py`)
- Orchestrates multiple API calls in parallel
- Builds intelligent queries from organization tokens
- Manages rate limits and quotas
- Returns normalized grant data

#### GrantFetcher (`grant_fetcher.py`)
- Scheduled bulk fetching (daily at 3 AM UTC)
- Fetches from all sources systematically
- Handles API failures gracefully
- Tracks fetch statistics

#### ScraperService (`scraper_service.py`)
- Web scraping for non-API sources
- HTML parsing with BeautifulSoup/Trafilatura
- Scheduled and on-demand scraping
- Watchlist-based targeting

### 3. **Data Processing & Persistence**

#### GrantDiscoveryServiceV2 (Primary Service)
```python
def discover_and_persist(org_id, limit=50, force_refresh=False):
    # 1. Check cache (24-hour window)
    if not force_refresh:
        cached = get_recent_grants(org_id)
        if cached: return cached
    
    # 2. Fetch from external sources
    grants = fetch_from_sources(org_id)
    
    # 3. Deduplicate
    for grant in grants:
        existing = check_existing(grant.url, grant.title)
        if existing:
            update_if_needed(existing)
        else:
            create_new_grant(grant)
    
    # 4. Apply AI scoring
    if new_grants:
        ai_score_grants(new_grants)
    
    return grants
```

#### Deduplication Strategy
- Primary: Match by `source_url`
- Secondary: Match by `title` + `funder`
- Updates allowed after 24 hours
- Duplicates still returned but not re-scored

### 4. **Database Schema**

#### Grant Model Fields
```sql
grants table:
- id: Integer (Primary Key)
- org_id: Foreign Key to organizations
- title: String(500)
- funder: String(255)
- amount_min/max: Numeric(14,2)
- deadline: Date
- status: Enum (discovery/writing/submitted/awarded)
- match_score: Integer (1-5)
- match_reason: Text
- contact_email, contact_phone, contact_name
- source_name, source_url
- created_at, updated_at
```

### 5. **AI Enhancement**

#### AI Scoring Pipeline
1. **REACTO Prompt Generation**: Structured prompts with organization context
2. **GPT-3.5/4 Processing**: Cost-optimized model selection
3. **Score Assignment**: 1-5 rating with explanation
4. **Batch Processing**: 15 grants at a time to prevent timeouts

#### Contact Extraction
- Regex patterns for emails, phones, names
- Department and organization extraction
- Confidence scoring (high/medium/low)
- Alternate contact detection

### 6. **Performance & Scale**

#### Current Stats
- **Discovery Rate**: 15-50 grants per API call
- **Persistence**: ~1 second for 15 grants
- **AI Scoring**: 15-20 seconds for 15 grants
- **Database**: 900+ grants scored, 16 active per org

#### Optimization Features
- **Smart Caching**: 24-hour cache window
- **Parallel Processing**: Multiple API calls simultaneously
- **Batch Operations**: Bulk inserts and updates
- **Error Resilience**: Graceful fallbacks for each source

## Workflow Example

### User Triggers Discovery
1. User clicks "Discover Grants" button
2. Frontend calls `/api/matching/discover/1`
3. GrantDiscoveryServiceV2 checks cache
4. If stale, fetches from APIs:
   - MatchingService assembles queries
   - Calls Candid, Grants.gov, foundations
   - Returns 15-50 grants
5. Persistence layer:
   - Deduplicates against existing
   - Creates/updates grant records
   - Returns grant IDs
6. AI scoring:
   - Batches grants for scoring
   - Applies REACTO prompts
   - Updates match scores
7. Returns to frontend:
   - Sorted by match score
   - Includes all metadata
   - Ready for Smart Tools

### Scheduled Discovery
- **Scheduler**: Runs daily at 3 AM UTC
- **Process**: Same as manual but for all organizations
- **Volume**: Processes 1000+ grants per run
- **Updates**: Refreshes scores for existing grants

## Error Handling

### API Failures
- Individual source failures don't stop discovery
- Falls back to cached data when available
- Logs failures for monitoring

### Rate Limiting
- Candid: 1000 calls/day limit
- Grants.gov: No hard limit
- SAM.gov: 10,000 calls/day
- Automatic throttling implemented

### Data Quality
- Quality score field (0-100)
- Contact confidence scoring
- Verification timestamps
- Source tracking for audit

## Future Enhancements

1. **Additional Sources**
   - EU funding portals
   - Canadian grants
   - Private foundation RSS feeds

2. **Intelligence Layer**
   - Funder relationship mapping
   - Success rate predictions
   - Competitive intelligence

3. **Performance**
   - Redis caching layer
   - Elasticsearch for search
   - Async job processing

## Testing

### Test Endpoints
- `/api/matching/test/{org_id}`: Pipeline validation
- `/api/matching/stats/{org_id}`: Discovery statistics
- `/api/grant-matching/batch`: Force AI scoring

### Current Test Results
```
✅ Discovery: 16 grants returned
✅ AI Scoring: 10/10 grants scored (avg 1.7/5)
✅ Smart Tools: 16 grants available
✅ Persistence: Deduplication working
✅ Caching: 24-hour window active
```

This architecture ensures comprehensive grant discovery with high reliability, intelligent scoring, and efficient data management at scale.
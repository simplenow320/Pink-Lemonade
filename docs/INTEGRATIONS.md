# GrantFlow API Integrations

## Overview
This document describes the external API integrations used by GrantFlow for grant discovery and matching.

## Candid API Integration

### Candid News API
- **Endpoint**: `https://services.candid.org/pnd/news/v1/articles`
- **Purpose**: Discover grant opportunities and RFPs from philanthropic news
- **Fields Returned**:
  - `title`: Article title
  - `description`: Article summary
  - `url`: Link to full article
  - `published_date`: Publication date
  - `funder`: Organization mentioned
- **Rate Limits**: 
  - 100 requests per minute per key
  - Rotating key pool supported
- **Caching**: 5-minute cache window

### Candid Grants API
- **Endpoint**: `https://services.candid.org/grants/v1/transactions`
- **Purpose**: Analyze historical grant transactions for context
- **Fields Returned**:
  - `recipient_name`: Grantee organization
  - `funder_name`: Funder organization
  - `amount`: Grant amount
  - `grant_date`: Award date
  - `description`: Grant purpose
- **Rate Limits**: 
  - 100 requests per minute per key
  - Rotating key pool supported
- **Caching**: 5-minute cache window

## Grants.gov API Integration

### Search Opportunities (search2)
- **Endpoint**: `POST https://api.grants.gov/v1/api/search2`
- **Purpose**: Search federal grant opportunities
- **Request Payload**:
  ```json
  {
    "opportunity_status": "open",
    "keywords": ["youth", "education"],
    "funding_instruments": ["G"],
    "eligibilities": ["25"],
    "page_size": 25
  }
  ```
- **Fields Returned**:
  - `oppNumber`: Opportunity number
  - `oppTitle`: Opportunity title
  - `agency`: Funding agency
  - `cfdaList`: CFDA programs
  - `openDate`: Opening date
  - `closeDate`: Closing deadline
  - `awardFloor`: Minimum award
  - `awardCeiling`: Maximum award
  - `eligibilities`: Eligible applicant types
- **Rate Limits**: No documented limits, but reasonable usage recommended
- **Caching**: Not implemented (real-time data)

### Fetch Opportunity Details
- **Endpoint**: `POST https://api.grants.gov/v1/api/opportunity/{oppNumber}`
- **Purpose**: Get detailed information about a specific opportunity
- **Fields Returned**: All fields from search plus:
  - `synopsis`: Detailed description
  - `costSharing`: Cost sharing requirements
  - `contactInfo`: Contact information
  - `additionalInfo`: Additional information URL

## Key Rotation

### Setting Up API Keys
1. Navigate to Replit Secrets (padlock icon)
2. Add the following secrets:
   - `CANDID_GRANTS_KEYS`: Comma-separated list of Candid Grants API keys
   - `CANDID_NEWS_KEYS`: Comma-separated list of Candid News API keys
   - Example: `key1,key2,key3`

### Automatic Key Rotation
- Keys are rotated automatically on 401 (Unauthorized) or 429 (Rate Limit) errors
- System tries up to 2 different keys before failing
- Key index (not value) is logged for debugging

## Matching & Scoring Algorithm

### Score Components (0-100 points)
1. **Keyword Overlap** (0-40 points): Based on matching keywords between org profile and opportunity
2. **Geographic Alignment** (0-20 points): Location match between org and grant
3. **Eligibility Match** (0-15 points): Nonprofit eligibility confirmation
4. **Award Amount Fit** (0-15 points): Grant size appropriate for org budget
5. **Recency/Urgency** (0-10 points): Deadline proximity and opportunity freshness

### Cache Windows
- **Matching results**: 5-minute cache
- **Analytics context**: 5-minute cache
- **Candid API responses**: 5-minute cache
- Cache can be bypassed with `?refresh=1` parameter

## Logging

All API interactions log:
- Key index used (not the actual key)
- Endpoint URL hit
- HTTP status code
- Cache hit/miss status

Logs are at INFO level and available in application logs.
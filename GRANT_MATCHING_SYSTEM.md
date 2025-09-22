# GrantFlow - Complete Grant Matching System Developer Guide

## 🎯 **Overview**

GrantFlow is a comprehensive AI-powered grant management platform that combines traditional API-based grant discovery with intelligent web scraping and AI-enhanced matching. This document provides a complete technical overview of the grant matching system for developers.

## 🏗️ **System Architecture**

### **Dual Backend Architecture**
The system maintains two parallel backends for flexibility:

1. **Python Flask Backend** (`app/` directory)
   - Legacy system with sophisticated AI matching
   - REACTO prompt engineering
   - Advanced analytics and workflow management
   - SQLAlchemy ORM with PostgreSQL

2. **Node.js Express Backend** (`server/` directory) 
   - Modern JavaScript-based system
   - Enhanced security middleware
   - Integrated denominational scraping
   - RESTful API with comprehensive error handling

### **Frontend**
- **React 18** with functional components and hooks
- **Tailwind CSS** with Pink Lemonade branding
- **React Router** for SPA navigation
- **Chart.js** for analytics visualization

---

## 🔍 **Grant Matching System Components**

### **1. Data Sources Layer**

#### **Traditional API Sources** (12+ integrated)
```javascript
// Configured in server/config/apiConfig.js
const API_SOURCES = {
  candid: {
    name: 'Candid Foundation Directory',
    endpoint: 'https://api.candid.org/v1/',
    access: '28+ million grants, $2+ trillion',
    authentication: 'subscription_key'
  },
  grants_gov: {
    name: 'Grants.gov REST API', 
    endpoint: 'https://api.grants.gov/v1/',
    access: 'Federal grant opportunities',
    authentication: 'api_key'
  },
  sam_gov_opportunities: {
    name: 'SAM.gov Opportunities',
    endpoint: 'https://api.sam.gov/opportunities/v2/',
    access: 'Federal contracts and opportunities',
    authentication: 'api_key'
  },
  federal_register: {
    name: 'Federal Register API',
    endpoint: 'https://www.federalregister.gov/api/v1/',
    access: 'Government NOFOs and notices',
    authentication: 'none'
  }
  // ... 8 more sources
}
```

#### **Denominational Sources** (19 faith-based sources)
```javascript
// Implemented in server/services/denominationalScraper.js
const DENOMINATIONAL_SOURCES = [
  {
    name: 'John Templeton Foundation',
    url: 'https://www.templeton.org/grants',
    tags: ['interfaith', 'science', 'religion'],
    type: 'foundation'
  },
  {
    name: 'Lilly Endowment',
    url: 'https://lillyendowment.org/grants/',
    tags: ['christian', 'education', 'community'],
    type: 'foundation'
  },
  {
    name: 'Presbyterian Church (USA)',
    url: 'https://www.presbyterianmission.org/ministries/1001/',
    tags: ['presbyterian', 'new-churches', 'mission'],
    type: 'denomination'
  }
  // ... 16 more sources
]
```

### **2. Data Processing Layer**

#### **Ethical Web Scraping Service**
```javascript
class DenominationalScraper {
  async scrapeSource(source) {
    // Check robots.txt compliance
    const robotsAllowed = await this.checkRobotsTxt(source.url);
    if (!robotsAllowed) {
      return { status: 'skipped', reason: 'robots.txt disallows' };
    }
    
    // Rate limiting (10 requests/minute)
    await this.rateLimiter.waitForSlot();
    
    // Puppeteer-based scraping with respectful headers
    const page = await this.browser.newPage();
    await page.setUserAgent('GrantFlow-Bot/1.0 (Educational/Nonprofit Grant Discovery)');
    
    // Extract structured data
    const opportunities = await this.extractGrantOpportunities(url, html, source.name, source.tags);
    
    return { status: 'success', opportunities };
  }
}
```

#### **Scheduled Automation**
```javascript
// Runs every 3 days with staggered updates
class ScheduledScraper {
  initialize() {
    // Main scraping cycle - every 3 days at 2 AM
    this.scheduledJob = schedule.scheduleJob('0 2 */3 * *', async () => {
      await this.runScheduledScrape();
    });
    
    // Staggered updates - every 6 hours for different source groups
    this.staggeredJob = schedule.scheduleJob('0 */6 * * *', async () => {
      await this.runStaggeredScrape();
    });
  }
}
```

### **3. AI Matching Engine**

#### **REACTO Prompt System** (Python Backend)
```python
class ReactoPrompts:
    def grant_matching_prompt(self, org_context, grant_data):
        """
        R - Role: AI Grant Evaluation Specialist
        E - Example: Perfect match analysis with 4.8/5.0 scoring
        A - Application: 6-step evaluation process
        C - Context: Organization profile and grant requirements
        T - Tone: Professional, analytical, helpful
        O - Output: JSON with scores, explanations, next steps
        """
        return self._build_prompt(org_context, grant_data)
```

#### **AI-Enhanced Denominational Service** (Node.js Backend)
```javascript
class AIEnhancedDenominationalService {
  async matchGrantsForOrganization(organizationProfile, options = {}) {
    // Weighted scoring algorithm
    const matchingWeights = {
      denominationMatch: 0.3,        // Direct faith alignment
      faithTraditionMatch: 0.25,     // Broader tradition compatibility
      missionAlignment: 0.2,         // Purpose/mission fit
      geographicMatch: 0.15,         // Location eligibility
      fundingAmountMatch: 0.1        // Budget compatibility
    };
    
    // Calculate match scores for each grant
    const scoredGrants = [];
    for (const grant of allOpportunities) {
      const match = this.calculateMatchScore(organizationProfile, grant);
      
      if (match.score >= options.minScore) {
        scoredGrants.push({
          ...grant,
          match_score: match.score,
          match_verdict: this.getMatchVerdict(match.score),
          key_alignments: match.alignments,
          potential_challenges: match.challenges,
          next_steps: match.nextSteps
        });
      }
    }
    
    return scoredGrants.sort((a, b) => b.match_score - a.match_score);
  }
}
```

### **4. Integrated Search System**

#### **Unified Search Architecture**
```javascript
class IntegratedGrantSearch {
  async searchAllSources(searchParams, organizationProfile = null) {
    // Search traditional API sources
    const apiResults = await this.searchApiSources(query, filters, pagination);
    
    // Search denominational sources with AI enhancement
    const denominationalResults = await this.searchDenominationalSources(
      query, filters, organizationProfile
    );
    
    // Combine with intelligent deduplication
    const combinedResults = await this.combineResults(
      apiResults, denominationalResults, organizationProfile
    );
    
    // Apply source-based weighting and sort
    const sortedResults = this.sortResults(combinedResults, prioritizeDenominational);
    
    return {
      grants: sortedResults,
      metadata: {
        totalResults: combinedResults.length,
        apiSourceResults: apiResults.total,
        denominationalResults: denominationalResults.length,
        sources: this.getSourceSummary(combinedResults)
      }
    };
  }
  
  // Intelligent deduplication across sources
  deduplicateResults(grants) {
    const seen = new Set();
    const deduplicated = [];
    
    for (const grant of grants) {
      const fingerprint = this.createGrantFingerprint(grant);
      if (!seen.has(fingerprint)) {
        seen.add(fingerprint);
        deduplicated.push(grant);
      } else {
        // Prefer denominational sources or higher quality data
        const existingIndex = deduplicated.findIndex(g => 
          this.createGrantFingerprint(g) === fingerprint
        );
        if (this.shouldReplaceExisting(deduplicated[existingIndex], grant)) {
          deduplicated[existingIndex] = grant;
        }
      }
    }
    return deduplicated;
  }
}
```

---

## 🚀 **API Endpoints**

### **Core Grant Search**
```http
GET /api/grants/search?query=nonprofit&source=denominational&limit=20
```
**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "grant-uuid-123",
      "title": "Community Development Ministry Grant",
      "source": "Evangelical Covenant Church", 
      "match_score": 4.2,
      "match_verdict": "Highly Recommended",
      "key_alignments": ["Direct denominational match", "Mission alignment: community development"],
      "funding_amount": "$50,000",
      "deadline": "2024-03-15",
      "application_url": "https://covchurch.org/apply"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "hasMore": true
  }
}
```

### **Denominational Grant Management**
```http
# Get scraping status
GET /api/denominational/status

# Get all denominational grants with filters
GET /api/denominational/grants?tag=presbyterian&amount_min=10000

# Search denominational grants
GET /api/denominational/search?q=youth ministry&limit=10

# Manual scraping trigger (requires auth)
POST /api/denominational/scrape
{
  "source": "John Templeton Foundation"  // Optional - all sources if omitted
}

# Get source configuration
GET /api/denominational/sources

# Get scraping history
GET /api/denominational/history?limit=5
```

### **Grant Discovery (Smart Matching)**
```http
POST /api/grants/discover
{
  "organizationProfile": {
    "name": "Urban Faith Community Center",
    "denomination": "methodist",
    "location": "Chicago, IL",
    "annualBudget": 500000,
    "focusAreas": ["youth programs", "community outreach", "social justice"],
    "missionStatement": "Serving urban communities through faith-based programs"
  },
  "preferences": {
    "prioritizeDenominational": true,
    "minScore": 3.0
  }
}
```

---

## 📊 **Data Models**

### **Grant Data Structure**
```javascript
const GrantModel = {
  // Core identification
  id: 'uuid',
  title: 'string',
  source: 'string',
  source_type: 'api | denominational',
  source_category: 'faith_based | federal_grants | foundation_database',
  
  // Content
  description: 'text',
  eligibility: 'text',
  funding_amount: 'string', // "$50,000" or "up to $100K"
  deadline: 'date | "rolling"',
  status: 'open | closed | pending',
  
  // Location & targeting
  geography: 'string', // "national", "Illinois", etc.
  tags: ['array', 'of', 'strings'], // Faith/program tags
  
  // Application
  application_url: 'url',
  contact_info: {
    email: 'email@foundation.org',
    phone: '(555) 123-4567'
  },
  
  // AI Enhancement (when available)
  match_score: 'number (0-5)', // AI-calculated match quality
  match_percentage: 'number (0-100)', // User-friendly percentage
  match_verdict: 'string', // "Highly Recommended" | "Consider Applying" | etc.
  match_reason: 'string', // Human-readable explanation
  key_alignments: ['array', 'of', 'strengths'],
  potential_challenges: ['array', 'of', 'concerns'],
  next_steps: ['array', 'of', 'actions'],
  denominational_priority: 'number (0-3)', // Denominational relevance boost
  ai_confidence: 'number (0-1)', // AI confidence in scoring
  
  // Metadata
  last_updated: 'timestamp',
  unique_key: 'string', // For deduplication
  created_at: 'timestamp'
}
```

### **Organization Profile Structure**
```javascript
const OrganizationProfile = {
  name: 'string',
  denomination: 'string', // "methodist", "presbyterian", "catholic", etc.
  organizationType: 'string', // "church", "nonprofit", "ministry"
  location: 'string', // "City, State" or "State"
  annualBudget: 'number',
  focusAreas: ['array', 'of', 'program', 'areas'],
  missionStatement: 'text',
  
  // Optional additional context
  established: 'year',
  staffSize: 'number',
  currentPrograms: ['array'],
  pastGrantExperience: 'boolean',
  capacityLevel: 'startup | growing | established | mature'
}
```

---

## 🔧 **Configuration & Environment**

### **Required Environment Variables**
```bash
# Node.js Backend
PORT=3001
NODE_ENV=development
JWT_SECRET=your-jwt-secret-key

# Frontend Configuration
FRONTEND_URL=http://localhost:3000  # Production only

# API Credentials (add incrementally)
CANDID_API_KEY=your-candid-key
CANDID_SUBSCRIPTION_KEY=your-candid-subscription
GRANTS_GOV_API_KEY=your-grants-gov-key
SAM_GOV_API_KEY=your-sam-gov-key

# Optional Services
REDIS_URL=redis://localhost:6379  # For caching and rate limiting
```

### **Package Dependencies** 
```json
{
  "dependencies": {
    "express": "^4.18.0",
    "puppeteer": "^21.0.0",
    "cheerio": "^1.0.0",
    "node-schedule": "^2.1.0",
    "axios": "^1.6.0",
    "helmet": "^7.0.0",
    "cors": "^2.8.0",
    "uuid": "^9.0.0",
    "winston": "^3.10.0"
  }
}
```

---

## 🚦 **Development Workflow**

### **1. Setup**
```bash
# Install dependencies
cd server
npm install

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Start development server
npm run dev  # Starts on port 3001
```

### **2. Adding New API Sources**
```javascript
// In server/config/apiConfig.js
export const API_SOURCES = {
  your_new_source: {
    name: 'Your New Grant Source',
    endpoint: 'https://api.example.com/v1/',
    authentication: {
      type: 'api_key',
      key: process.env.YOUR_SOURCE_API_KEY
    },
    enabled: !!process.env.YOUR_SOURCE_API_KEY,
    rateLimits: {
      requestsPerMinute: 60,
      requestsPerHour: 1000
    }
  }
};
```

### **3. Adding New Denominational Sources**
```javascript
// In server/services/denominationalScraper.js
this.sources = [
  // ... existing sources
  {
    name: 'Your New Foundation',
    url: 'https://newfoundation.org/grants',
    additionalUrls: [
      'https://newfoundation.org/apply',
      'https://newfoundation.org/guidelines'
    ],
    tags: ['christian', 'education', 'youth'],
    type: 'foundation'
  }
];
```

### **4. Testing**
```bash
# Run smoke tests
npm test

# Test specific endpoints
curl http://localhost:3001/api/health
curl http://localhost:3001/api/denominational/status
curl "http://localhost:3001/api/grants/search?query=youth&limit=5"
```

---

## 🔍 **AI Matching Algorithm Details**

### **Scoring Methodology**
The AI matching system uses a weighted scoring approach:

1. **Denominational Match (30%)**: Direct faith tradition alignment
   - Perfect denomination match: 5.0 points
   - Compatible faith tradition: 4.0 points  
   - Interfaith/ecumenical compatibility: 3.0 points

2. **Mission Alignment (20%)**: Program focus and purpose alignment
   - Keyword matching between org mission and grant description
   - Focus area overlap (youth, community, education, etc.)
   - Impact area compatibility

3. **Faith Tradition Match (25%)**: Broader theological compatibility
   - Progressive/Liberal traditions
   - Evangelical/Conservative traditions
   - Mainline Protestant traditions
   - Catholic/Orthodox traditions

4. **Geographic Match (15%)**: Location-based eligibility
   - National programs: 5.0 points
   - Regional match: 4.0 points
   - State-specific: 3.0 points

5. **Funding Amount Match (10%)**: Budget compatibility
   - Grant amount <= 50% org budget: 5.0 points
   - Grant amount <= org budget: 4.0 points
   - Grant amount <= 200% org budget: 2.0 points

### **Match Verdict Categories**
- **4.0+ points**: "Highly Recommended" - Strong alignment across multiple criteria
- **3.0-3.9 points**: "Recommended" - Good fit with solid alignment
- **2.5-2.9 points**: "Consider Applying" - Moderate fit worth exploring
- **2.0-2.4 points**: "Worth Exploring" - Some alignment, review carefully
- **<2.0 points**: "Low Priority" - Limited alignment

### **Faith Tradition Mappings**
```javascript
const faithTraditions = {
  'christian': ['catholic', 'protestant', 'orthodox', 'evangelical'],
  'protestant': ['baptist', 'methodist', 'presbyterian', 'episcopal', 'lutheran'],
  'progressive': ['progressive', 'liberal', 'inclusive', 'social-justice'],
  'evangelical': ['evangelical', 'conservative', 'fundamentalist'],
  'interfaith': ['ecumenical', 'multi-faith', 'interfaith', 'interreligious']
};
```

---

## 🛡️ **Security & Compliance**

### **API Security**
- **Helmet.js**: Security headers and CSP
- **Rate Limiting**: Per-endpoint rate limits
- **Input Sanitization**: XSS and injection protection
- **CORS**: Configured for development and production origins
- **Authentication**: JWT-based auth for sensitive endpoints

### **Scraping Ethics**
- **Robots.txt Compliance**: Automatic checking before scraping
- **Rate Limiting**: Respectful request rates (10/minute max)
- **User Agent**: Proper identification as educational tool
- **No Personal Data**: Only public grant information collected
- **Terms Compliance**: Respects foundation terms of service

### **Data Privacy**
- **No Personal Storage**: Organization profiles not persisted without consent
- **API Key Security**: All credentials server-side only
- **Audit Logging**: Complete audit trail for scraping activities
- **Error Handling**: Sensitive data never exposed in error messages

---

## 📈 **Performance Optimizations**

### **Caching Strategy**
```javascript
// Cache configuration
const cacheManager = new CacheManager();

// API results cached for 1 hour
cacheManager.set('api_search_results', results, 3600000);

// Denominational data cached for 24 hours  
cacheManager.set('denominational_grants', data, 86400000);

// Robots.txt cached for 1 hour per domain
cacheManager.set(`robots:${domain}`, allowed, 3600000);
```

### **Circuit Breakers**
```javascript
// Automatic failure handling
const circuitBreaker = new CircuitBreaker({
  failureThreshold: 5,    // Open after 5 failures
  timeout: 30000,         // 30 second timeout
  resetTimeout: 60000     // Try again after 1 minute
});
```

### **Database Optimization** (Python Backend)
```python
# Optimized queries with proper indexing
class Grant(db.Model):
    # Indexes for fast searching
    __table_args__ = (
        db.Index('idx_grants_deadline', 'deadline'),
        db.Index('idx_grants_match_score', 'match_score'),
        db.Index('idx_grants_org_id', 'org_id'),
        db.Index('idx_grants_created_at', 'created_at'),
    )
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

**1. Scraping Not Working**
```bash
# Check scraping status
curl http://localhost:3001/api/denominational/status

# Common causes:
# - Robots.txt blocking (check logs)
# - Rate limits exceeded (wait and retry)  
# - Site structure changed (update selectors)
# - Network connectivity issues
```

**2. Missing Search Results**
```bash
# Verify data sources
curl http://localhost:3001/api/sources/status

# Check API credentials
curl http://localhost:3001/api/config/credentials

# Verify circuit breakers
curl http://localhost:3001/api/config/circuit-breakers
```

**3. AI Scoring Issues**
```javascript
// Check if organization profile is complete
const requiredFields = ['denomination', 'focusAreas', 'location', 'missionStatement'];
const missingFields = requiredFields.filter(field => !organizationProfile[field]);

if (missingFields.length > 0) {
  console.log('Missing profile fields:', missingFields);
  // AI scoring will be less accurate
}
```

### **Debugging Tools**
```bash
# Enable debug logging
NODE_ENV=development DEBUG=* npm start

# Check application logs
tail -f server/logs/combined.log

# Monitor scraping activity
tail -f data/scraped/*.json
```

---

## 🔄 **Data Flow Summary**

```
External APIs     →  API Manager       →  Integrated Search  →  Frontend
     ↓                    ↓                      ↑              
Denominational    →  Scheduled Scraper →  AI Enhancement    →  User Interface
Web Sources          (Every 3 days)         (Matching)         
     ↓                    ↓                      ↑
Data Storage      →  Cache Manager     →  Response Formatter →  React Components
(Files/Cache)        (Redis/Memory)        (JSON API)          
```

### **Request Flow Example**
1. User searches for "youth ministry grants"
2. Frontend sends request to `/api/grants/search?query=youth ministry`
3. IntegratedGrantSearch processes request:
   - Searches API sources via ApiManager
   - Searches denominational sources from cached scrape data
   - Applies AI scoring if organization profile provided
   - Deduplicates and combines results
   - Sorts by relevance and denominational priority
4. Response formatted and returned to frontend
5. React components render grant cards with match scores

---

## 📚 **Additional Resources**

- **Python REACTO System**: `app/services/reacto_prompts.py`
- **AI Matching Logic**: `app/services/ai_grant_matcher.py` 
- **API Documentation**: Swagger docs at `/api/docs` (when enabled)
- **Foundation Source List**: `data/foundation_sources.csv`
- **Scraping Results**: `data/scraped/` directory
- **Error Logs**: `server/logs/error.log`

---

## 🏁 **Quick Start Checklist**

1. ✅ **Environment Setup**: Configure `.env` with required variables
2. ✅ **Dependencies**: Run `npm install` in server directory  
3. ✅ **API Keys**: Add at least 2-3 API credentials for testing
4. ✅ **Start Server**: `npm start` - should start on port 3001
5. ✅ **Test Endpoints**: Verify `/api/health` responds successfully
6. ✅ **Check Sources**: Visit `/api/sources/status` to see enabled sources
7. ✅ **Test Search**: Try `/api/grants/search?query=test&limit=5`
8. ✅ **Verify Scraping**: Check `/api/denominational/status` 
9. ✅ **Frontend Connection**: Ensure React app can reach backend
10. ✅ **Monitor Logs**: Watch `server/logs/` for any issues

**Your integrated grant matching system is now ready for development!** 🚀

---

*This documentation covers the complete GrantFlow grant matching system. For specific implementation details, refer to the individual service files in the codebase.*
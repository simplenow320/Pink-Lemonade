# Run Now Button Implementation

## Overview
The "Run Now" button has been implemented in the Grants page to allow manual triggering of the grant scraper service.

## Features
- **Manual Trigger**: Click "Run Now" to immediately scrape for new grant opportunities
- **Optional Search**: Enter a search query to filter the scraping to specific grants
- **Toast Notifications**: Shows success/error messages with number of opportunities found
- **Auto-Refresh**: Automatically refreshes the opportunities list after scraping
- **Pink Lemonade Branding**: Consistent pink color scheme throughout

## API Integration
```javascript
POST /api/scrape/run-now
Body: { 
  orgId: number,  // Required: Organization ID
  query?: string  // Optional: Search query
}

Response: {
  orgId: number,
  query?: string,
  upserted: number,  // Number of new/updated grants
  mode: 'LIVE' | 'DEMO'
}
```

## Components

### Toast Component (`components/Toast.js`)
- Displays temporary notifications
- Auto-dismisses after 5 seconds
- Supports success, error, and info types

### Grants Page (`pages/Grants.js`)
- Main opportunities discovery interface
- Run Now button in header
- Optional search input
- Opportunities list with:
  - Title, funder, deadline
  - Amount ranges
  - Match scores (1-5 with color coding)
  - Direct links to grant details

## Usage
1. Navigate to the Grants page
2. (Optional) Enter a search term
3. Click "Run Now" button
4. View toast notification with results
5. Browse refreshed opportunities list

## Next Steps
- Integrate with user authentication for dynamic orgId
- Add filters for deadline, amount, location
- Implement saved searches
- Add batch selection for applications
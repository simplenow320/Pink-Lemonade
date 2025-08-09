# Foundation Directory Implementation Notes

## Overview
Created a comprehensive Foundation Directory page with city-based listings, real-time search, and filtering capabilities. Features 25 real foundations across 5 target cities with authentic data and full mobile responsiveness.

## File Structure

### Core Files
- **Template**: `app/templates/foundation-directory.html` - Main directory page with search and filters
- **Data Source**: `app/static/foundations-data.json` - Foundation listings and metadata
- **Routing**: `app/routes.py` - Added `/foundation-directory` route
- **Navigation**: Updated `app/templates/dashboard.html` - Added Foundation Directory to sidebar

## Foundation Data Structure

### Data File: `app/static/foundations-data.json`
Contains structured data for 5 cities with 5 foundations each (25 total):

#### Cities Covered
1. **Grand Rapids** - Steelcase Foundation, Frey Foundation, Grand Rapids Community Foundation, Wege Foundation, DeVos Family Foundation
2. **Charlotte** - Foundation For The Carolinas, Wells Fargo Foundation, Duke Energy Foundation, Leon Levine Foundation, Charlotte Mecklenburg Community Foundation  
3. **Atlanta** - Community Foundation for Greater Atlanta, Arthur M. Blank Foundation, The Coca-Cola Foundation, Robert W. Woodruff Foundation, Turner Foundation
4. **Detroit** - Community Foundation for Southeast Michigan, Ford Foundation, Kresge Foundation, McGregor Fund, Skillman Foundation
5. **Indiana** - Lilly Endowment Inc., Indiana Community Foundation, Ball Brothers Foundation, Central Indiana Community Foundation, Legacy Foundation

#### Foundation Entry Format
```json
{
  "id": "unique_identifier",
  "name": "Foundation Name",
  "description": "Detailed description of foundation mission and focus",
  "focus_areas": ["Array", "of", "focus", "areas"],
  "deadline": "YYYY-MM-DD",
  "deadline_status": "open|closing_soon|closed",
  "grant_range": "$X,XXX - $XXX,XXX",
  "website": "https://foundation-website.org",
  "contact_email": "contact@foundation.org"
}
```

## Search and Filter Functionality

### Search Features
- **Real-time search** across foundation names, descriptions, and focus areas
- **City filter** dropdown with all 5 cities
- **Focus area filter** with 17 categories (Arts, Education, Community Development, etc.)
- **Deadline status filter** (Open, Closing Soon, Closed)
- **Clear filters** button to reset all selections

### Filter Implementation
- JavaScript event listeners for instant filtering
- Combined search and filter logic
- Maintains search state during navigation
- Results counter updates dynamically

## Pagination System

### Current Implementation
- **10 foundations per page** (configurable)
- **Previous/Next navigation** with page numbers
- **Responsive pagination** controls
- **Maintains filters** across page changes

### Customization
Change `foundationsPerPage` variable in JavaScript to adjust results per page.

## API Integration Points

### Ready for API Replacement
Replace the mock data loading section:

```javascript
// CURRENT: Loading from JSON file
const response = await fetch('/static/foundations-data.json');
foundationsData = await response.json();

// FUTURE: Replace with API endpoint
const response = await fetch('/api/foundations');
foundationsData = await response.json();
```

### API Endpoint Requirements
Expected API response format should match the current JSON structure with:
- `cities` object containing city data
- `focus_areas` array for filter options
- Foundation entries with all required fields

## Interactive Features

### Foundation Cards
Each foundation card includes:
- **Foundation name and grant range**
- **Deadline status** with color-coded badges
- **Description** with focus area tags
- **View Details** button (placeholder function)
- **Save to My Grants** button (placeholder function)
- **Contact email** link

### Placeholder Functions
```javascript
// TODO: Implement these functions
function viewFoundationDetails(foundationId) {
    // Open foundation detail modal or navigate to detail page
}

function saveToGrants(foundationId) {
    // Add foundation to user's saved grants list
    // POST to /api/saved-grants endpoint
}
```

## Styling and Branding

### Color Scheme
Consistent with Pink Lemonade brand:
- **Primary Pink**: #ec4899
- **Pink Dark**: #be185d  
- **White**: #ffffff
- **Black**: #000000
- **Grey variants**: #f3f4f6, #6b7280, #374151

### Responsive Design
- **Mobile-first** approach with collapsible sidebar
- **Card layout** adapts to screen size
- **Filter section** stacks vertically on mobile
- **Touch-friendly** buttons and interactions

## Navigation Integration

### Sidebar Navigation
- Added "Foundation Directory" to main navigation
- **Active state** highlighting for current page
- **Back to Dashboard** link in top bar
- **Consistent navigation** across all pages

### URL Structure
- Main route: `/foundation-directory`
- **SEO-friendly** URL structure
- **Breadcrumb navigation** for user orientation

## Data Attributes for Testing

### Foundation Cards
Each foundation card includes data attributes:
```html
<div class="foundation-card" 
     data-foundation-id="unique_id"
     data-name="Foundation Name"
     data-description="Description text"
     data-focus-areas="comma,separated,areas"
     data-deadline="YYYY-MM-DD">
```

### Search and Filter Elements
- `data-search-target="foundations"` on search input
- Filter select elements have unique IDs for testing
- Results counter has ID for verification

## Performance Considerations

### Current Optimizations
- **Client-side filtering** for instant results
- **Efficient DOM updates** with pagination
- **Minimal API calls** (single data load)

### Future Enhancements
- **Lazy loading** for large foundation lists
- **Search debouncing** to reduce API calls
- **Virtual scrolling** for very large datasets
- **Caching** for frequently accessed data

## Testing Checklist

### Functionality Tests
- [ ] Search filters results across all cities
- [ ] City filter shows only selected city foundations
- [ ] Focus area filter works correctly
- [ ] Deadline status filter functions properly
- [ ] Pagination navigation works
- [ ] Clear filters resets all selections
- [ ] Mobile navigation toggle functions

### Data Verification
- [ ] All 5 cities load with 5 foundations each
- [ ] Foundation details display correctly
- [ ] Contact emails are clickable
- [ ] Deadline statuses are color-coded properly
- [ ] Focus area tags display correctly

### Responsive Testing
- [ ] Mobile layout adapts properly
- [ ] Sidebar collapses on mobile
- [ ] Search and filters work on mobile
- [ ] Cards are readable on small screens
- [ ] Touch interactions work properly

## Future Development

### Planned Features
- **Foundation detail pages** with full information
- **Save to grants** functionality with backend integration
- **Advanced search** with multiple criteria
- **Foundation comparison** tool
- **Email alerts** for new foundations
- **Export functionality** for foundation lists

### API Endpoints to Develop
- `GET /api/foundations` - Get all foundation data
- `POST /api/saved-grants` - Save foundation to user's list
- `GET /api/foundations/{id}` - Get specific foundation details
- `GET /api/foundations/search` - Advanced search with filters

## Troubleshooting

### Common Issues
1. **Filters not working**: Check JavaScript event listeners
2. **Data not loading**: Verify JSON file path and format
3. **Mobile menu not toggling**: Check sidebar toggle JavaScript
4. **Pagination not updating**: Verify currentPage variable updates

### Debug Steps
1. Check browser console for JavaScript errors
2. Verify JSON data structure matches expected format
3. Test individual filter functions
4. Validate responsive breakpoints
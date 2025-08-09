# Dashboard Implementation Notes

## Overview
Created a comprehensive dashboard view with API-ready placeholders and configurable text content that matches the Pink Lemonade branding and design system.

## File Structure

### Core Dashboard Files
- **Template**: `app/templates/dashboard.html` - Main dashboard HTML structure
- **Configuration**: `app/static/dashboard-config.json` - All editable text and labels  
- **Mock Data**: `app/static/mock-data.json` - Sample data for layout preview
- **Routing**: `app/routes.py` - Updated to serve dashboard at `/dashboard`

## Configuration Management

### Editing Text Content
All user-facing text can be updated in `app/static/dashboard-config.json`:

```json
{
  "branding": {
    "title": "Pink Lemonade",
    "welcome_message": "Welcome back, {{username}}!"
  },
  "navigation": {
    "dashboard": "Dashboard",
    "grants_feed": "Grants Feed", 
    "saved_opportunities": "Saved Opportunities",
    "my_applications": "My Applications",
    "settings": "Settings"
  },
  "widgets": {
    "grants_feed": {
      "title": "Latest Grant Opportunities",
      "subtitle": "Fresh funding opportunities matched to your mission"
    }
    // ... additional widget text
  }
}
```

### Variable Replacement
- `{{username}}` in welcome message will be replaced with actual user data
- Edit `dashboard-config.json` to update all text without touching code

## Widget Structure & API Integration

Each widget has a `data-source` attribute for easy API swapping:

### 1. Grants Feed Widget
- **HTML Selector**: `[data-source="grants-api"]`
- **Container**: `#grants-container`
- **API Endpoint**: Replace fetch call in `populateGrantsFeed()` function
- **Expected Data Format**: Array of grant objects with `title`, `funder`, `amount`, `deadline`, `match_score`

### 2. Foundation Directory Widget  
- **HTML Selector**: `[data-source="foundation-directory-api"]`
- **Container**: `#foundation-container`
- **API Endpoint**: Replace fetch call in `populateFoundationDirectory()` function
- **Expected Data Format**: Array with `city` and nested `foundations` array

### 3. Deadlines Widget
- **HTML Selector**: `[data-source="deadlines-api"]`
- **Container**: `#deadlines-container` 
- **API Endpoint**: Replace fetch call in `populateDeadlines()` function
- **Expected Data Format**: Array with `grant_title`, `deadline`, `days_remaining`, `status`

### 4. Saved Grants Widget
- **HTML Selector**: `[data-source="saved-grants-api"]`
- **Container**: `#saved-grants-container`
- **API Endpoint**: Replace fetch call in `populateSavedGrants()` function
- **Expected Data Format**: Array with `title`, `funder`, `amount`, `match_score`, `saved_date`

### 5. AI Recommendations Widget
- **HTML Selector**: `[data-source="ai-recommendations-api"]`
- **Container**: `#ai-recommendations-container`
- **API Endpoint**: Replace fetch call in `populateAIRecommendations()` function
- **Expected Data Format**: Array with `grant_title`, `match_percentage`, `reasoning`, `funder`, `deadline`

## API Integration Instructions

### Step 1: Replace Mock Data Calls
In `app/templates/dashboard.html`, locate each populate function and replace:

```javascript
// FROM:
const mockResponse = await fetch('/static/mock-data.json');
mockData = await mockResponse.json();

// TO:
const apiResponse = await fetch('/api/your-endpoint');
const apiData = await apiResponse.json();
```

### Step 2: Update Function Logic
Each populate function expects specific data structures. Ensure your API returns data matching the expected format or adapt the rendering logic accordingly.

### Step 3: Error Handling
Add proper error handling for API failures:

```javascript
try {
    const response = await fetch('/api/endpoint');
    if (!response.ok) throw new Error('API Error');
    const data = await response.json();
    // Process data
} catch (error) {
    console.error('Error loading data:', error);
    // Show fallback UI
}
```

## Navigation System

### Navigation Menu
- **Collapsible sidebar** with responsive mobile hamburger menu
- **Active state management** via CSS classes
- **Route handling** ready for single-page app navigation

### Navigation Items
1. Dashboard (active by default)
2. Grants Feed  
3. Saved Opportunities
4. My Applications
5. Settings

### Adding New Navigation Items
Edit the navigation section in `dashboard-config.json` and add corresponding HTML in the sidebar nav section.

## Responsive Design

### Breakpoints
- **Mobile**: < 768px - Collapsible sidebar, simplified layout
- **Tablet**: 768px - 1024px - Adjusted grid layout  
- **Desktop**: > 1024px - Full 3-column grid layout

### Mobile Optimizations
- Sidebar converts to slide-out menu
- Top navigation includes hamburger menu
- Grid layouts stack vertically
- Text sizes adjust appropriately

## Styling System

### CSS Variables
Consistent with landing page color scheme:
```css
:root {
    --primary: #4a5568;
    --secondary: #718096; 
    --accent: #5a67d8;
    --background: #f7fafc;
    --surface: #ffffff;
    --text-primary: #2d3748;
    --text-secondary: #4a5568;
    --border: #e2e8f0;
}
```

### Component Classes
- `.widget-card` - Standard widget container
- `.grant-item` - Individual grant listing
- `.match-score` - Grant match percentage badge
- `.nav-item` - Sidebar navigation items
- `.deadline-urgent/upcoming/planned` - Deadline status colors

## Testing Checklist

### Layout Testing
- [ ] Desktop layout displays properly
- [ ] Mobile responsiveness works
- [ ] Sidebar collapse/expand functions
- [ ] All widgets render correctly
- [ ] Typography is consistent

### Functionality Testing  
- [ ] Mock data loads in all widgets
- [ ] City selector populates foundation directory
- [ ] Navigation highlighting works
- [ ] Mobile menu toggle functions
- [ ] Console shows no JavaScript errors

### Integration Testing
- [ ] Config file changes update text
- [ ] Data-source attributes present
- [ ] API placeholder functions identified
- [ ] Error handling implemented

## Future Enhancements

### Additional Features
- User profile management
- Real-time notifications
- Grant application tracking
- Export/import functionality
- Advanced filtering and search

### Performance Optimizations
- Lazy loading for large data sets
- Caching for frequently accessed data
- Progressive web app features
- Offline functionality

## Troubleshooting

### Common Issues
1. **Mock data not loading**: Check file paths in `app/static/`
2. **Styling issues**: Verify CSS variable declarations
3. **Mobile menu not working**: Check JavaScript event listeners
4. **Text not updating**: Ensure config file is properly formatted JSON

### Debug Steps
1. Check browser console for JavaScript errors
2. Verify all files are in correct locations
3. Test API endpoints independently
4. Validate JSON configuration files
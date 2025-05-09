# GrantFlow Frontend

This directory contains the React frontend for the GrantFlow application.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   npm start
   ```

The frontend will be available at [http://localhost:3000](http://localhost:3000)

## Project Structure

- `public/` - Static assets
- `src/` - Source code
  - `components/` - React components
  - `hooks/` - Custom React hooks
  - `utils/` - Utility functions
  - `App.js` - Main application component
  - `index.js` - Entry point

## Development Guidelines

- Follow component-based architecture
- Use React hooks for state management
- Use the proxy configuration for API calls
- Follow tailwind configuration for styling

## Available Scripts

- `npm start` - Start development server
- `npm test` - Run tests
- `npm run build` - Build for production
- `npm run eject` - Eject from Create React App

## API Integration

The frontend communicates with the Flask backend using the proxy configuration in `package.json`. This means you can make API calls to endpoints without specifying the full URL:

```javascript
// Instead of:
fetch('http://localhost:5000/api/grants')

// You can use:
fetch('/api/grants')
```

## Environment Variables

Create a `.env.local` file in this directory to set environment variables for the React application. For example:

```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_VERSION=1.0.0
```

These variables must be prefixed with `REACT_APP_` to be accessible in the React application.
# GrantFlow Client

The frontend React application for GrantFlow, a grant management platform for nonprofits.

## Setup & Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create a .env file from the example:
   ```bash
   cp .env.example .env
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## Error Handling

GrantFlow uses a robust error handling system:

### ApiError Class

Use the `ApiError` class from `utils/api.js` for API-related errors:

```javascript
import { ApiError } from '../utils/api';

throw new ApiError('User-friendly error message', 404, originalError);
```

### ErrorBoundary

Wrap components with `ErrorBoundary` to catch runtime errors:

```jsx
import ErrorBoundary from '../components/ErrorBoundary';

<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

For a custom fallback UI, use the `fallback` prop:

```jsx
<ErrorBoundary
  fallback={(error) => <div>Custom error UI: {error.message}</div>}
  resetAction={() => navigate('/')}
  resetButtonText="Go Home"
>
  <YourComponent />
</ErrorBoundary>
```

### SafeComponent

For a simpler approach, use the `SafeComponent` wrapper:

```jsx
import SafeComponent from '../components/SafeComponent';

<SafeComponent
  fallbackTitle="Component Error"
  resetButtonText="Try Again"
  onError={(error) => logError(error)}
  resetAction={() => resetComponentState()}
>
  <YourComponent />
</SafeComponent>
```

### Notification Context

Use the notification context for displaying toast-style messages:

```jsx
import { useNotification } from '../context/NotificationContext';

function MyComponent() {
  const { addSuccess, addError, addWarning, addInfo } = useNotification();
  
  const handleAction = () => {
    try {
      // Do something
      addSuccess('Operation completed successfully!');
    } catch (error) {
      addError(error.message);
    }
  };
  
  return (
    // ...
  );
}
```

## Development Tools

### Linting & Formatting

- Run ESLint:
  ```bash
  npm run lint
  ```

- Fix ESLint issues:
  ```bash
  npm run lint:fix
  ```

- Format code with Prettier:
  ```bash
  npm run format
  ```

### Testing

- Run tests:
  ```bash
  npm test
  ```

- Run tests with coverage:
  ```bash
  npm run test:coverage
  ```

## Environment Variables

The application uses the following environment variables:

- `REACT_APP_API_URL`: The base URL for API calls (defaults to '/api' if not set)
- `REACT_APP_ENABLE_DEBUG_TOOLS`: Enable debug tools (boolean, defaults to false)

These can be set in the `.env` file in the project root.
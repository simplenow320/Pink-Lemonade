// Simple React test component
console.log('React test script loading...');

function SimpleTest() {
  return React.createElement('div', {
    style: {
      padding: '2rem',
      textAlign: 'center',
      background: 'white',
      margin: '2rem',
      borderRadius: '8px',
      boxShadow: '0 2px 10px r#e5e7eb'
    }
  }, 
    React.createElement('h1', { style: { color: '#007bff' } }, 'GrantFlow'),
    React.createElement('p', { style: { color: '#6c757d' } }, 'React is working! App is loading...'),
    React.createElement('button', {
      style: {
        background: '#007bff',
        color: 'white',
        border: 'none',
        padding: '0.75rem 1.5rem',
        borderRadius: '6px',
        cursor: 'pointer',
        marginTop: '1rem'
      },
      onClick: function() { alert('React event handling works!'); }
    }, 'Test Button')
  );
}

// Test render
console.log('Attempting to render simple test...');
console.log('React:', typeof React);
console.log('ReactDOM:', typeof ReactDOM);

try {
  const rootElement = document.getElementById('root');
  console.log('Root element found:', !!rootElement);
  
  if (rootElement) {
    ReactDOM.render(React.createElement(SimpleTest), rootElement);
    console.log('Simple test rendered successfully!');
  }
} catch (error) {
  console.error('Simple test failed:', error);
}
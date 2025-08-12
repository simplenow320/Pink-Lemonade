import os
from flask import send_from_directory, send_file
from app import create_app

# Create the Flask app using the factory function
app = create_app()

# Serve React App
@app.route('/')
def serve_react_app():
    try:
        return send_file('client/build/index.html')
    except:
        # If build doesn't exist, serve from public
        try:
            return send_file('client/public/index.html')
        except:
            # Fallback to templates
            return send_file('templates/index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('client/public/assets', filename)

# Catch all other routes and serve React app (for client-side routing)
@app.route('/<path:path>')
def catch_all(path):
    # Don't catch API routes
    if path.startswith('api/'):
        return {'error': 'API endpoint not found'}, 404
    try:
        return send_file('client/build/index.html')
    except:
        try:
            return send_file('client/public/index.html')
        except:
            return send_file('templates/index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

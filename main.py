from flask import send_from_directory, send_file, jsonify
from app import create_app
import os

# Create the Flask app using the factory function
app = create_app()

# Add a simple health check endpoint for deployment
@app.route('/health')
def health():
    """Simple health check for deployment monitoring"""
    return jsonify({
        'status': 'healthy',
        'message': 'Application is running'
    }), 200

# Register enhanced grant data blueprints
try:
    from app.api import enhanced_grant_data
    app.register_blueprint(enhanced_grant_data.bp)
except ImportError as e:
    print(f"Warning: Could not import enhanced_grant_data: {e}")

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

# Serve static files from React build
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('client/build/static', path)

# Catch all other routes and serve React app (for client-side routing)
@app.route('/<path:path>')
def catch_all(path):
    # Don't catch API routes - let blueprints handle them
    if path.startswith('api/'):
        from flask import abort
        abort(404)  # Let Flask handle 404 properly for API routes
    try:
        return send_file('client/build/index.html')
    except:
        try:
            return send_file('client/public/index.html')
        except:
            return send_file('templates/index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
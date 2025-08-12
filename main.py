from app import create_app

app = create_app()

# Register enhanced grant data blueprints
try:
    from app.api import enhanced_grant_data
    app.register_blueprint(enhanced_grant_data.bp)
except ImportError as e:
    print(f"Warning: Could not import enhanced_grant_data: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
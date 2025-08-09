import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.settings")  # keep your settings module

    CORS(app, supports_credentials=True)
    db.init_app(app)

    # Create tables within app context
    with app.app_context():
        # Import models so they are registered
        from app.models.grant import Grant
        from app.models.organization import Organization
        
        # Create all tables
        db.create_all()

    # register blueprints
    from app.api.grants import bp as grants_bp
    from app.api.orgs import bp as orgs_bp
    from app.api.discovery import bp as discovery_bp
    from app.api.ai import bp as ai_bp
    from app.api.watchlists import bp as watchlists_bp
    app.register_blueprint(grants_bp, url_prefix="/api/grants")
    app.register_blueprint(orgs_bp, url_prefix="/api/orgs")
    app.register_blueprint(discovery_bp, url_prefix="/api/discovery")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(watchlists_bp, url_prefix="/api/watchlists")

    # remove any "serve React for all routes" logic until the new React app is ready
    return app

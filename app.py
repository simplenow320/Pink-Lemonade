import os
from flask import Flask, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__, 
            static_folder='client/build/static',
            static_url_path='/static')

app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

# Serve React App
@app.route('/')
def serve_react_app():
    return send_file('client/build/index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('client/public/assets', filename)

# Catch all other routes and serve React app
@app.route('/<path:path>')
def catch_all(path):
    return send_file('client/build/index.html')

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    try:
        import models  # noqa: F401
        db.create_all()
    except ImportError:
        print("No models.py found - creating basic tables")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

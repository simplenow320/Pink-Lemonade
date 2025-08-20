
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import session, redirect, url_for, flash
from app.models import User

login_manager = LoginManager()

def init_login_manager(app):
    """Initialize Flask-Login with the app"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return login_manager

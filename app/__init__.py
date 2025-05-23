# app/__init__.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_seasurf import SeaSurf
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Route name for the login page (blueprint_name.view_function)
login_manager.login_message_category = 'info' # Bootstrap class for flash messages
csrf = SeaSurf() # CSRF protection for forms

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  
    login_manager.init_app(app)

    # Import and register the auth blueprint
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth') # All auth routes will be under /auth

    # Import and register the home blueprint
    from app.home import home_bp
    app.register_blueprint(home_bp, url_prefix='/home') # All home routes will be under /home

    # A simple route to about page
    @app.route('/')
    def index():
        return render_template('about.html', title='About Page')

    # Import models here to ensure they are known to Flask-Migrate
    # and for the shell context processor in run.py
    from app import models

    return app
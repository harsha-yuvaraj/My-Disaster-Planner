# app/__init__.py
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_seasurf import SeaSurf
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session
from mailjet_rest import Client as MailjetClient
from config import Config
from app.chatbot.chatbot_service import initialize_ai_services
import json
import boto3



db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Route name for the login page (blueprint_name.view_function)
login_manager.login_message_category = 'info' # Bootstrap class for flash messages
csrf = SeaSurf() # CSRF protection for forms
session = Session()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  
    login_manager.init_app(app)
    session.init_app(app)

    # --- Initialize Boto3 S3 Client (Eager Loading) --- 
    try:
        region = app.config['AWS_DEFAULT_REGION']
        app.s3_client = boto3.client('s3', region_name=region)
    except Exception as e:
        print(f"Failed to initialize Boto3 S3 client: {e}")
        app.s3_client = None 

    try:
        app.mailjet = MailjetClient(auth=(app.config['MAILJET_API_KEY'], app.config['MAILJET_API_SECRET']), version='v3.1')
    except Exception as e:
        print(f"Failed to initialize Mailjet client: {e}")
        app.mailjet = None 
    
    try:
        with open(app.config['FLORIDA_CEMW_JSON_PATH']) as f:
            app.config['FLORIDA_CEMW'] = json.load(f)
    except FileNotFoundError:
        print(f"FLORIDA_CEMW.json data file not found at: {app.config['FLORIDA_CEMW_JSON_PATH']}")
        app.config['FLORIDA_CEMW'] = {} # Default to an empty dict or handle as needed

    # This runs the AI chatbot initialization once and attaches the engine to the app context
    app.query_engine = initialize_ai_services(app)

    # Import and register the auth blueprint
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth') # All auth routes will be under /auth

    # Import and register the home blueprint
    from app.home import home_bp
    app.register_blueprint(home_bp, url_prefix='/home') # All home routes will be under /home

    # Import and register the chatbot blueprint
    from app.chatbot import chatbot_bp
    app.register_blueprint(chatbot_bp, url_prefix='/api') # All chatbot routes will be under /chatbot

    # A simple route to about page
    @app.route('/')
    def index():
        return redirect(url_for('auth.login')) # Redirect to the login page

    # Import models here to ensure they are known to Flask-Migrate
    # and for the shell context processor in run.py
    from app import models

    print("My Disaster Planner is ready and up...")

    return app
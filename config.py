# config.py
from decouple import config

class Config:
    SECRET_KEY = config('SECRET_KEY') 
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')
    MAILJET_API_KEY = config('MAILJET_API_KEY')
    MAILJET_API_SECRET = config('MAILJET_API_SECRET')
    DEFAULT_MAIL_SENDER = config('DEFAULT_MAIL_SENDER')
    MAIL_FROM_NAME = config('MAIL_FROM_NAME', default='My Disaster Planner') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    # Add any other configuration variables  below as needed
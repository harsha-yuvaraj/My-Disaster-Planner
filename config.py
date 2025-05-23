# config.py
from decouple import config

class Config:
    SECRET_KEY = config('SECRET_KEY') 
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')
    SENDGRID_API_KEY = config('SENDGRID_API_KEY')
    DEFAULT_MAIL_SENDER = config('DEFAULT_MAIL_SENDER')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    # Add any other configuration variables  below as needed
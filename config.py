# config.py
from decouple import config

class Config:
    SECRET_KEY = config('SECRET_KEY') 
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    # Add any other configuration variables  below as needed
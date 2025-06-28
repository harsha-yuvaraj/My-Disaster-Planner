# config.py
from decouple import config
import os

# Get the absolute path of the directory where this config.py file is located
basedir = os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY = config('SECRET_KEY') 
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')
    MAILJET_API_KEY = config('MAILJET_API_KEY')
    MAILJET_API_SECRET = config('MAILJET_API_SECRET')
    DEFAULT_MAIL_SENDER = config('DEFAULT_MAIL_SENDER')
    MAIL_FROM_NAME = config('MAIL_FROM_NAME', default='My Disaster Planner') 
    GOOGLE_API_KEY = config('GOOGLE_API_KEY')
    GOOGLE_ROUTES_API_URL = config('GOOGLE_ROUTES_API_URL')
    GOOGLE_GEOCODE_API_URL = config('GOOGLE_GEOCODE_API_URL')
    GOOGLE_ROUTES_API_URL = config('GOOGLE_ROUTES_API_URL')
    FEMA_NFHL_IDENTIFY_URL = config('FEMA_NFHL_IDENTIFY_URL')
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = config('AWS_DEFAULT_REGION', default='us-east-1')
    S3_BUCKET_NAME = config('S3_BUCKET_NAME')  
    FLORIDA_CEMW_JSON_PATH = os.path.join(basedir, 'app', 'data', 'FLORIDA_CEMW.json')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    # Add any other configuration variables  below as needed
# Application Configuration
import os
from pathlib import Path

basedir = Path(__file__).parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Handle both PostgreSQL (Render) and SQLite (local)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render provides postgres:// but SQLAlchemy needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{basedir / "instance" / "farmers_portal.db"}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = basedir / 'app' / 'static' / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Crop images upload path
    CROP_IMAGES_FOLDER = UPLOAD_FOLDER / 'crops'
    
    # ML datasets upload path
    ML_DATASETS_FOLDER = UPLOAD_FOLDER / 'ml_datasets'
    
    # Product images upload path
    PRODUCT_IMAGES_FOLDER = UPLOAD_FOLDER / 'products'
    
    # OpenWeatherMap API
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY') or None
    WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'
    WEATHER_FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'


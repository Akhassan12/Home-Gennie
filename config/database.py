"""
Database Configuration Module
Handles both SQLite (development) and PostgreSQL (production)
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('FLASK_ENV') == 'development'
    
    @staticmethod
    def get_database_uri():
        """
        Get database URI based on environment
        Returns PostgreSQL URI if available, else SQLite
        """
        db_url = os.environ.get('DATABASE_URL')
        
        # If DATABASE_URL is set in env, use it (priority to PostgreSQL)
        if db_url and 'postgresql' in db_url:
            return db_url
        
        # Fallback to SQLite for development
        instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        db_path = os.path.join(instance_path, 'ar_interior.db')
        
        # Use absolute path for SQLite
        return f'sqlite:///{db_path.replace(chr(92), "/")}'  # Convert backslashes to forward slashes


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


def get_config():
    """Get appropriate config based on FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()

"""
Configuration module for Cloud-Based Digital Library Backend
Handles environment variables and AWS configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the Flask application"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
    COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration variables are set"""
        required_vars = [
            'COGNITO_USER_POOL_ID',
            'COGNITO_CLIENT_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Validate configuration on import
try:
    Config.validate_config()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file and ensure all required variables are set.")

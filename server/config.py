import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # AWS / Cognito
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
    # Match usage in routes: Config.COGNITO_CLIENT_ID
    COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    @classmethod
    def validate_config(cls):
        required_vars = ['COGNITO_USER_POOL_ID', 'COGNITO_CLIENT_ID']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        return True

# Fail fast on misconfiguration
Config.validate_config()

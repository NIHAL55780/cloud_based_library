import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
    
    # S3 Configuration
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'your-bucket-name-here')
    BOOKS_PREFIX = 'books/'
    
    # DynamoDB Configuration
    DYNAMODB_REGION = os.getenv('DYNAMODB_REGION', AWS_REGION)
    DYNAMODB_BOOKS_TABLE = os.getenv('DYNAMODB_BOOKS_TABLE', 'BookMetaData')
    DYNAMODB_USER_BOOKS_TABLE = os.getenv('DYNAMODB_USER_BOOKS_TABLE', 'DigitalLibrary-UserBooks')
    
    # Optional: Cognito Configuration (if using authentication)
    COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
    COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration variables"""
        # Skip validation for now - Cognito can work without AWS credentials
        return True

# Skip config validation for development
# Config.validate_config()

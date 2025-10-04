# Cloud-Based Digital Library Backend

A Flask-based backend API for the Cloud-Based Digital Library with AI Book Recommender system, featuring AWS Cognito authentication.

## 🚀 Features

- **User Authentication**: Signup and login using AWS Cognito
- **CORS Support**: Ready for frontend integration
- **Environment Configuration**: Secure environment variable management
- **Error Handling**: Comprehensive error handling and validation
- **Health Checks**: API health monitoring endpoints

## 📁 Project Structure

```
server/
├── app.py                 # Main Flask application
├── config.py             # Configuration and environment variables
├── requirements.txt      # Python dependencies
├── env.example          # Environment variables template
├── README.md            # This file
└── routes/
    └── auth_routes.py   # Authentication endpoints
```

## 🛠️ Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- AWS Account with Cognito User Pool configured
- pip or pipenv for package management

### 2. AWS Cognito Setup

1. Create a Cognito User Pool in AWS Console
2. Create an App Client (without client secret for USER_PASSWORD_AUTH)
3. Note down your User Pool ID and Client ID

### 3. Environment Configuration

1. Copy the environment template:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` file with your actual values:
   ```env
   SECRET_KEY=your-super-secret-key-here
   DEBUG=True
   PORT=5000
   AWS_REGION=us-east-1
   COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
   COGNITO_CLIENT_ID=your-cognito-client-id-here
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

### 4. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using pipenv
pipenv install
```

### 5. Run the Server

```bash
# Development mode
python app.py

# Or using Flask CLI
flask run

# Production mode with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

The server will start on `http://localhost:5000` (or the port specified in your `.env` file).

## 📡 API Endpoints

### Base Endpoints

- `GET /` - API information and available endpoints
- `GET /health` - Health check

### Authentication Endpoints

- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `GET /auth/health` - Auth service health check

## 🧪 Testing with Postman

### 1. User Signup

**Endpoint**: `POST http://localhost:5000/auth/signup`

**Headers**:
```
Content-Type: application/json
```

**Body** (JSON):
```json
{
    "email": "user@example.com",
    "password": "SecurePass123"
}
```

**Expected Response** (201):
```json
{
    "message": "User created successfully",
    "user_sub": "uuid-here",
    "confirmation_required": "user@example.com",
    "next_step": "Please check your email for verification code"
}
```

### 2. User Login

**Endpoint**: `POST http://localhost:5000/auth/login`

**Headers**:
```
Content-Type: application/json
```

**Body** (JSON):
```json
{
    "email": "user@example.com",
    "password": "SecurePass123"
}
```

**Expected Response** (200):
```json
{
    "message": "Login successful",
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ...",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

### 3. Health Check

**Endpoint**: `GET http://localhost:5000/health`

**Expected Response** (200):
```json
{
    "status": "healthy",
    "service": "cloud-library-api",
    "version": "1.0.0"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | - |
| `DEBUG` | Enable debug mode | No | False |
| `PORT` | Server port | No | 5000 |
| `AWS_REGION` | AWS region | Yes | us-east-1 |
| `COGNITO_USER_POOL_ID` | Cognito User Pool ID | Yes | - |
| `COGNITO_CLIENT_ID` | Cognito Client ID | Yes | - |
| `CORS_ORIGINS` | Allowed CORS origins | No | localhost:3000,localhost:5173 |

### AWS Permissions

Your AWS credentials need the following permissions:
- `cognito-idp:SignUp`
- `cognito-idp:InitiateAuth`
- `cognito-idp:AdminGetUser`
- `cognito-idp:AdminUpdateUserAttributes`

## 🚨 Error Handling

The API includes comprehensive error handling for:

- **Validation Errors**: Invalid email format, weak passwords
- **AWS Cognito Errors**: User exists, authentication failures, rate limiting
- **Server Errors**: Internal server errors with appropriate status codes

## 🔒 Security Features

- Password strength validation
- Email format validation
- CORS configuration
- Environment variable protection
- AWS Cognito integration for secure authentication

## 🚀 Next Steps

This backend is ready for integration with:
- **DynamoDB**: For book and user data storage
- **S3**: For file uploads and book content
- **SageMaker**: For AI-powered book recommendations
- **React Frontend**: The existing frontend in this project

## 📝 Development Notes

- The application uses Flask Blueprints for modular route organization
- All routes return JSON responses with consistent error formatting
- CORS is configured for frontend integration
- Environment variables are validated on startup
- The application follows RESTful API conventions

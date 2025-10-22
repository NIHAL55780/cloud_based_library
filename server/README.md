# Digital Library Backend

A Flask-based REST API backend for a digital library with AWS Cognito authentication and S3 integration for secure book access.

## Features

- **Authentication**: AWS Cognito integration for user management
- **S3 Integration**: Generate pre-signed URLs for secure book access
- **REST API**: Clean RESTful endpoints for library operations
- **CORS Support**: Configured for frontend integration
- **Error Handling**: Comprehensive error handling and logging
- **Health Checks**: Built-in health monitoring endpoints

## Prerequisites

- Python 3.8 or higher
- AWS Account with Cognito and S3 access
- AWS credentials (Access Key ID and Secret Access Key)

## Installation

1. **Clone the repository and navigate to the server directory:**
   ```bash
   cd server
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your actual values
   ```

## Configuration

### Environment Variables

Create a `.env` file in the server directory with the following variables:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
DEBUG=True
PORT=5000

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# S3 Configuration
S3_BUCKET_NAME=your-bucket-name-here

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Optional: Cognito Configuration (if using authentication)
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=your-cognito-client-id-here
```

### AWS S3 Setup

1. **Create an S3 Bucket:**
   - Bucket name: `your-bucket-name-here` (or update `S3_BUCKET_NAME` in .env)
   - Region: Must match your `AWS_REGION`

2. **Upload Books:**
   - Upload your PDF files to the `books/` prefix in your S3 bucket
   - Example structure:
     ```
     your-bucket-name-here/
     └── books/
         ├── book1.pdf
         ├── book2.pdf
         └── book3.pdf
     ```

3. **IAM Permissions:**
   Your AWS user/role needs the following permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::your-bucket-name-here",
           "arn:aws:s3:::your-bucket-name-here/*"
         ]
       }
     ]
   }
   ```

### AWS Cognito Setup (Optional)

1. **Create a Cognito User Pool:**
   - Set up user pool in AWS Cognito
   - Configure authentication settings
   - Note the User Pool ID and Client ID

2. **Configure Authentication:**
   - Update `COGNITO_USER_POOL_ID` and `COGNITO_CLIENT_ID` in your `.env` file
   - The application supports both Cognito-based and mock authentication

## Running the Application

1. **Start the Flask server:**
   ```bash
   python app.py
   ```

2. **The server will start on:**
   - URL: `http://localhost:5000`
   - Debug mode: Enabled (if DEBUG=True in .env)

## API Endpoints

### Base Information
- **GET** `/` - API information and available endpoints
- **GET** `/health` - Health check endpoint

### Library Endpoints

#### Get All Books
- **GET** `/books`
- **Description**: List all available books from S3
- **Headers**: `Authorization: Bearer <jwt_token>` (optional)
- **Response**: JSON with list of books and metadata

#### Get Book URL
- **GET** `/book/<filename>`
- **Description**: Generate pre-signed URL for a specific book
- **Headers**: `Authorization: Bearer <jwt_token>` (optional)
- **Response**: JSON with pre-signed URL and expiration time

#### Health Check
- **GET** `/health`
- **Description**: Check the health of S3 services
- **Response**: JSON with service status

## Authentication

The application supports multiple authentication methods:

1. **AWS Cognito**: Full Cognito integration with JWT verification
2. **Public Cognito**: Direct HTTP calls to Cognito (no AWS credentials required)
3. **Mock Authentication**: Simple in-memory authentication for development

## File Structure

```
server/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── env.example          # Environment variables template
├── test_library_api.py  # API test suite
├── routes/
│   ├── auth_routes.py        # Cognito authentication routes
│   ├── auth_routes_public.py # Public Cognito routes
│   ├── auth_routes_mock.py   # Mock authentication routes
│   └── library_routes.py     # Library management routes with S3
└── README.md            # This file
```

## Error Handling

The API includes comprehensive error handling for:
- Authentication errors
- S3 service errors
- Invalid request parameters
- Configuration issues

All errors return JSON responses with appropriate HTTP status codes.

## Security Considerations

- **Pre-signed URLs**: Short-lived (1 hour) URLs prevent unauthorized access
- **Authentication**: JWT tokens are verified before granting access
- **CORS**: Configured for specific frontend origins
- **Environment Variables**: Sensitive credentials stored in environment variables

## File Naming Convention

The backend attempts to parse book metadata from filenames using the format:
`title_author_genre.pdf`

Example: `The-Great-Gatsby_F-Scott-Fitzgerald_Fiction.pdf`

If the filename doesn't match this pattern, it will use the filename as the title and set author/genre as "Unknown".

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in your environment
2. Use a production WSGI server like Gunicorn
3. Configure proper logging
4. Use IAM roles instead of access keys
5. Set up proper CORS origins for your domain
6. Configure Cognito User Pool for production

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**: Ensure your `.env` file has correct AWS credentials
2. **S3 Bucket Not Found**: Verify the bucket name and region match your configuration
3. **CORS Errors**: Check that your frontend URL is included in `CORS_ORIGINS`
4. **Authentication Issues**: Verify Cognito User Pool and Client ID configuration

### Logs

The application logs important events and errors. Check the console output for debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.
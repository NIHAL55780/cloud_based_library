# Cloud-Based Digital Library Backend

A Flask-based REST API backend for a cloud-based digital library that integrates with AWS S3 for file storage and DynamoDB for metadata management.

## Features

- **File Upload**: Upload PDF and JPG files to AWS S3
- **Metadata Management**: Store and retrieve book metadata in DynamoDB
- **REST API**: Clean RESTful endpoints for all operations
- **CORS Support**: Configured for frontend integration
- **Error Handling**: Comprehensive error handling and logging
- **Health Checks**: Built-in health monitoring endpoints

## Prerequisites

- Python 3.8 or higher
- AWS Account with S3 and DynamoDB access
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

# AWS Services
S3_BUCKET_NAME=cloud-library-files
DYNAMODB_TABLE_NAME=BooksMetadata

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### AWS Setup

1. **Create an S3 Bucket:**
   - Bucket name: `cloud-library-files` (or update `S3_BUCKET_NAME` in .env)
   - Region: Must match your `AWS_REGION`
   - Configure public read access for uploaded files

2. **Create a DynamoDB Table:**
   - Table name: `BooksMetadata`
   - Primary key: `BookID` (String)
   - Attributes: `Title`, `Author`, `Genre`, `Description`, `S3URL`, `UploadDate`

3. **IAM Permissions:**
   Your AWS user/role needs the following permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:PutObjectAcl",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:HeadBucket"
         ],
         "Resource": "arn:aws:s3:::cloud-library-files/*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "dynamodb:PutItem",
           "dynamodb:GetItem",
           "dynamodb:Scan",
           "dynamodb:Query"
         ],
         "Resource": "arn:aws:dynamodb:us-east-1:*:table/BooksMetadata"
       }
     ]
   }
   ```

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
- **Description**: Retrieve all books from the database
- **Response**: JSON with list of books and count

#### Get Book by ID
- **GET** `/books/<book_id>`
- **Description**: Retrieve a specific book by its ID
- **Parameters**: `book_id` (string) - The unique book identifier
- **Response**: JSON with book metadata

#### Upload Book
- **POST** `/upload`
- **Description**: Upload a new book file to S3 and add metadata to DynamoDB
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file` (required): PDF or JPG file
  - `title` (required): Book title
  - `author` (required): Book author
  - `genre` (required): Book genre
  - `description` (optional): Book description
- **Response**: JSON with upload status and book metadata

#### Health Check
- **GET** `/health`
- **Description**: Check the health of AWS services
- **Response**: JSON with service status

## Example Usage

### Upload a Book
```bash
curl -X POST http://localhost:5000/upload \
  -F "file=@example.pdf" \
  -F "title=Example Book" \
  -F "author=John Doe" \
  -F "genre=Fiction" \
  -F "description=A great example book"
```

### Get All Books
```bash
curl http://localhost:5000/books
```

### Get Specific Book
```bash
curl http://localhost:5000/books/123e4567-e89b-12d3-a456-426614174000
```

## Testing

Run the test suite to verify all endpoints:

```bash
python test_library_api.py
```

The test script will:
- Check server connectivity
- Test all API endpoints
- Verify error handling
- Provide a summary of results

## File Structure

```
server/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── env.example          # Environment variables template
├── test_library_api.py  # API test suite
├── routes/
│   ├── auth_routes.py   # Authentication routes
│   └── library_routes.py # Library management routes
└── README.md            # This file
```

## Error Handling

The API includes comprehensive error handling for:
- Missing or invalid files
- AWS service errors
- Database connection issues
- Invalid request parameters
- File type validation

All errors return JSON responses with appropriate HTTP status codes.

## Security Considerations

- Files are validated for type and size
- AWS credentials are loaded from environment variables
- CORS is configured for specific origins
- File names are sanitized before upload
- S3 files are set to public read (consider private buckets for production)

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in your environment
2. Use a production WSGI server like Gunicorn
3. Configure proper logging
4. Use IAM roles instead of access keys
5. Enable S3 bucket encryption
6. Configure DynamoDB backup and monitoring
7. Set up proper CORS origins for your domain

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**: Ensure your `.env` file has correct AWS credentials
2. **S3 Bucket Not Found**: Verify the bucket name and region match your configuration
3. **DynamoDB Table Not Found**: Ensure the table exists with the correct name and primary key
4. **CORS Errors**: Check that your frontend URL is included in `CORS_ORIGINS`

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
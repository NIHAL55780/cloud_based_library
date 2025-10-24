# DynamoDB Integration for Digital Library

This document explains how to integrate AWS DynamoDB with your digital library for enhanced metadata storage and user interactions.

## 🎯 **Why DynamoDB?**

- **Serverless**: No infrastructure management
- **AWS Native**: Seamless integration with S3 and Cognito
- **Fast Queries**: Sub-millisecond response times
- **Auto-scaling**: Handles traffic spikes automatically
- **Cost-effective**: Pay per request, not per server
- **Rich Metadata**: Store complex book and user data

## 📊 **Database Schema**

### **Books Table (`DigitalLibrary-Books`)**
```json
{
  "book_id": "uuid",
  "filename": "s3-key",
  "title": "string",
  "author": "string", 
  "genre": "string",
  "publication_year": "number",
  "language": "string",
  "description": "text",
  "isbn": "string",
  "cover_url": "url",
  "tags": ["array"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### **User-Books Table (`DigitalLibrary-UserBooks`)**
```json
{
  "user_id": "string",
  "book_id": "string",
  "rating": "number",
  "review": "text",
  "bookmarked": "boolean",
  "reading_progress": "number",
  "date_added": "datetime",
  "date_rated": "datetime"
}
```

## 🚀 **Quick Setup**

### **1. Install Dependencies**
```bash
pip install boto3
```

### **2. Configure Environment**
```bash
# Copy environment template
cp env.example .env

# Edit .env with your AWS credentials
DYNAMODB_REGION=us-east-1
DYNAMODB_BOOKS_TABLE=DigitalLibrary-Books
DYNAMODB_USER_BOOKS_TABLE=DigitalLibrary-UserBooks
```

### **3. Run Setup Script**
```bash
python setup_dynamodb.py
```

This will:
- Create DynamoDB tables
- Migrate existing S3 data
- Verify the migration

## 🔧 **Manual Setup**

### **1. Create Tables**
```python
from dynamodb_setup import DynamoDBManager

db_manager = DynamoDBManager()
db_manager.create_tables()
```

### **2. Migrate Data**
```python
from migrate_to_dynamodb import S3ToDynamoDBMigrator

migrator = S3ToDynamoDBMigrator()
result = migrator.migrate_all_books()
```

## 📡 **API Endpoints**

### **Enhanced Book Management**

#### **Get All Books**
```http
GET /books
```
**Response:**
```json
{
  "success": true,
  "count": 10,
  "books": [
    {
      "book_id": "uuid",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "genre": "Fiction",
      "filename": "the-great-gatsby.pdf",
      "s3_size": 1024000,
      "s3_last_modified": "2024-01-01T00:00:00Z"
    }
  ],
  "source": "dynamodb"
}
```

#### **Search Books**
```http
GET /books/search?q=gatsby&author=Fitzgerald&genre=Fiction
```

#### **Get Specific Book**
```http
GET /books/{book_id}
```

#### **Update Book Metadata**
```http
PUT /books/{book_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "author": "Updated Author",
  "genre": "Updated Genre",
  "description": "Updated description"
}
```

### **User Interactions**

#### **Get Bookmarks**
```http
GET /bookmarks
X-User-ID: user123
```

#### **Add Bookmark**
```http
POST /bookmarks/{book_id}
X-User-ID: user123
```

#### **Rate Book**
```http
POST /books/{book_id}/rate
X-User-ID: user123
Content-Type: application/json

{
  "rating": 5,
  "review": "Excellent book!"
}
```

## 🔍 **Advanced Features**

### **1. Smart Search**
```python
# Search by multiple criteria
books = db_manager.search_books_by_author("Fitzgerald")
books = db_manager.search_books_by_genre("Fiction")
```

### **2. User Analytics**
```python
# Get user's reading history
bookmarks = db_manager.get_user_bookmarks("user123")
ratings = db_manager.get_user_ratings("user123")
```

### **3. Metadata Enrichment**
```python
# Auto-detect genre from filename
genre = detect_genre_from_text("The-Great-Gatsby_F-Scott-Fitzgerald_Fiction.pdf")
# Returns: "Fiction"
```

## 📈 **Performance Benefits**

### **Before (S3-only)**
- ❌ Slow metadata extraction from filenames
- ❌ No user-specific data
- ❌ Limited search capabilities
- ❌ No analytics

### **After (S3 + DynamoDB)**
- ✅ Fast metadata queries (< 10ms)
- ✅ Rich user interactions
- ✅ Advanced search and filtering
- ✅ Analytics and recommendations
- ✅ Scalable to millions of books

## 🔒 **Security & Permissions**

### **IAM Permissions Required**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/DigitalLibrary-Books",
        "arn:aws:dynamodb:us-east-1:*:table/DigitalLibrary-UserBooks"
      ]
    }
  ]
}
```

## 💰 **Cost Estimation**

### **DynamoDB Pricing (US East 1)**
- **On-Demand**: $0.25 per million read requests
- **On-Demand**: $1.25 per million write requests
- **Storage**: $0.25 per GB per month

### **Example Usage (1,000 books, 100 users)**
- **Monthly Reads**: ~100,000 requests = $0.025
- **Monthly Writes**: ~10,000 requests = $0.0125
- **Storage**: ~1GB = $0.25
- **Total**: ~$0.29/month

## 🛠 **Troubleshooting**

### **Common Issues**

#### **1. Tables Not Created**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify DynamoDB permissions
aws dynamodb list-tables
```

#### **2. Migration Failed**
```bash
# Check S3 permissions
aws s3 ls s3://your-bucket-name/books/

# Run migration with debug
python migrate_to_dynamodb.py
```

#### **3. API Errors**
```python
# Test DynamoDB connection
from dynamodb_setup import DynamoDBManager
db_manager = DynamoDBManager()
books = db_manager.get_all_books()
print(f"Found {len(books)} books")
```

## 🔄 **Migration Strategy**

### **Phase 1: Setup (1 day)**
1. Create DynamoDB tables
2. Run migration script
3. Verify data integrity

### **Phase 2: Integration (2-3 days)**
1. Update Flask routes
2. Test new endpoints
3. Update frontend

### **Phase 3: Enhancement (1 week)**
1. Add user authentication
2. Implement advanced search
3. Add analytics dashboard

## 📚 **Next Steps**

1. **Run the setup script**: `python setup_dynamodb.py`
2. **Update your Flask app** to use the new routes
3. **Test the new endpoints** with your frontend
4. **Add user authentication** for personalized features
5. **Implement advanced search** and filtering
6. **Add analytics** for usage insights

## 🆘 **Support**

If you encounter issues:
1. Check the logs in `server/logs/`
2. Verify AWS credentials and permissions
3. Test individual components with the provided scripts
4. Review the troubleshooting section above

---

**Ready to enhance your digital library with DynamoDB? Run `python setup_dynamodb.py` to get started!** 🚀

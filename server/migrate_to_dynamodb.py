"""
Migration Script: S3 to DynamoDB
Migrates existing S3 book metadata to DynamoDB with enhanced metadata
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import uuid

from config import Config
from dynamodb_setup import DynamoDBManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3ToDynamoDBMigrator:
    def __init__(self):
        """Initialize migrator with S3 and DynamoDB clients"""
        self.s3_client = boto3.client('s3')
        self.db_manager = DynamoDBManager(region_name=Config.DYNAMODB_REGION)
        
    def migrate_all_books(self) -> Dict[str, Any]:
        """Migrate all books from S3 to DynamoDB"""
        logger.info("Starting migration from S3 to DynamoDB...")
        
        try:
            # Create DynamoDB tables if they don't exist
            logger.info("Creating DynamoDB tables...")
            self.db_manager.create_tables()
            
            # Get all books from S3
            logger.info("Fetching books from S3...")
            s3_books = self.get_s3_books()
            
            # Migrate each book
            migrated_count = 0
            failed_count = 0
            errors = []
            
            for book_data in s3_books:
                try:
                    success = self.migrate_single_book(book_data)
                    if success:
                        migrated_count += 1
                        logger.info(f"✅ Migrated: {book_data.get('title', 'Unknown')}")
                    else:
                        failed_count += 1
                        logger.error(f"❌ Failed: {book_data.get('filename', 'Unknown')}")
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Error migrating {book_data.get('filename', 'Unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            result = {
                'success': True,
                'total_books': len(s3_books),
                'migrated': migrated_count,
                'failed': failed_count,
                'errors': errors
            }
            
            logger.info(f"Migration completed: {migrated_count}/{len(s3_books)} books migrated")
            return result
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_s3_books(self) -> List[Dict[str, Any]]:
        """Get all books from S3 with metadata"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=Config.S3_BUCKET_NAME,
                Prefix=Config.BOOKS_PREFIX
            )
            
            books = []
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('/'):
                    continue
                
                filename = obj['Key'].replace(Config.BOOKS_PREFIX, '')
                
                # Get S3 object metadata
                try:
                    head_response = self.s3_client.head_object(
                        Bucket=Config.S3_BUCKET_NAME,
                        Key=obj['Key']
                    )
                    s3_metadata = head_response.get('Metadata', {})
                except Exception as e:
                    logger.warning(f"Could not get metadata for {filename}: {e}")
                    s3_metadata = {}
                
                # Parse filename for metadata
                parsed_metadata = self.parse_filename_metadata(filename)
                
                # Combine S3 metadata with parsed metadata
                book_data = {
                    'filename': filename,
                    's3_size': obj['Size'],
                    's3_last_modified': obj['LastModified'].isoformat(),
                    's3_content_type': obj.get('ContentType', 'application/pdf'),
                    **s3_metadata,  # S3 object metadata
                    **parsed_metadata  # Parsed from filename
                }
                
                books.append(book_data)
            
            return books
            
        except Exception as e:
            logger.error(f"Error getting books from S3: {e}")
            return []
    
    def parse_filename_metadata(self, filename: str) -> Dict[str, Any]:
        """Parse filename to extract metadata (enhanced version)"""
        try:
            name_without_ext = filename.replace('.pdf', '')
            
            # Enhanced parsing logic
            title = name_without_ext
            author = "Unknown"
            genre = "General"
            language = "English"
            publication_year = None
            
            # Pattern 1: "Author - Title"
            if ' - ' in name_without_ext:
                parts = name_without_ext.split(' - ')
                if len(parts) == 2:
                    author = parts[0].strip()
                    title = parts[1].strip()
            
            # Pattern 2: "Title by Author"
            elif ' by ' in name_without_ext.lower():
                parts = name_without_ext.split(' by ')
                if len(parts) == 2:
                    title = parts[0].strip()
                    author = parts[1].strip()
            
            # Pattern 3: "Title_Author_Genre"
            elif '_' in name_without_ext:
                parts = name_without_ext.split('_')
                if len(parts) >= 2:
                    title = parts[0].replace('-', ' ')
                    if len(parts) >= 3:
                        author = ' '.join(parts[1:-1]).replace('-', ' ')
                        genre = parts[-1].replace('-', ' ').title()
                    else:
                        author = parts[1].replace('-', ' ')
            
            # Pattern 4: "Title, Author"
            elif ',' in name_without_ext:
                parts = name_without_ext.split(',')
                if len(parts) == 2:
                    title = parts[0].strip()
                    author = parts[1].strip()
            
            # Genre detection
            genre = self.detect_genre_from_text(name_without_ext)
            
            # Year detection
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', name_without_ext)
            if year_match:
                publication_year = int(year_match.group())
            
            return {
                'book_id': str(uuid.uuid4()),
                'title': title,
                'author': author,
                'genre': genre,
                'language': language,
                'publication_year': publication_year,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error parsing filename {filename}: {e}")
            return {
                'book_id': str(uuid.uuid4()),
                'title': filename.replace('.pdf', ''),
                'author': 'Unknown',
                'genre': 'General',
                'language': 'English',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
    
    def detect_genre_from_text(self, text: str) -> str:
        """Detect genre from text content"""
        text_lower = text.lower()
        
        genre_keywords = {
            'Fiction': ['fiction', 'novel', 'story', 'tale'],
            'Mystery': ['mystery', 'detective', 'crime', 'thriller', 'suspense'],
            'Romance': ['romance', 'love', 'relationship'],
            'Science Fiction': ['sci-fi', 'science fiction', 'space', 'future', 'alien'],
            'Fantasy': ['fantasy', 'magic', 'wizard', 'dragon', 'mythical'],
            'Biography': ['biography', 'autobiography', 'memoir', 'life story'],
            'History': ['history', 'historical', 'war', 'ancient'],
            'Philosophy': ['philosophy', 'wisdom', 'knowledge', 'truth'],
            'Self-Help': ['self-help', 'motivation', 'success', 'personal development'],
            'Business': ['business', 'management', 'finance', 'economics'],
            'Technology': ['technology', 'programming', 'computer', 'software'],
            'Health': ['health', 'medical', 'fitness', 'wellness'],
            'Education': ['education', 'learning', 'teaching', 'academic']
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return genre
        
        return 'General'
    
    def migrate_single_book(self, book_data: Dict[str, Any]) -> bool:
        """Migrate a single book to DynamoDB"""
        try:
            # Check if book already exists
            existing_book = self.db_manager.get_book_by_filename(book_data['filename'])
            if existing_book:
                logger.info(f"Book {book_data['filename']} already exists in DynamoDB, skipping...")
                return True
            
            # Add book to DynamoDB
            success = self.db_manager.add_book(book_data)
            return success
            
        except Exception as e:
            logger.error(f"Error migrating book {book_data.get('filename', 'Unknown')}: {e}")
            return False
    
    def backup_existing_data(self) -> bool:
        """Create a backup of existing data before migration"""
        try:
            logger.info("Creating backup of existing data...")
            
            # Get all books from S3
            s3_books = self.get_s3_books()
            
            # Save to JSON file
            backup_filename = f"backup_s3_books_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(s3_books, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Backup created: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verify that migration was successful"""
        try:
            logger.info("Verifying migration...")
            
            # Get books from DynamoDB
            dynamodb_books = self.db_manager.get_all_books()
            
            # Get books from S3
            s3_books = self.get_s3_books()
            
            verification_result = {
                's3_books_count': len(s3_books),
                'dynamodb_books_count': len(dynamodb_books),
                'migration_successful': len(dynamodb_books) >= len(s3_books),
                'missing_books': [],
                'extra_books': []
            }
            
            # Check for missing books
            s3_filenames = {book['filename'] for book in s3_books}
            dynamodb_filenames = {book['filename'] for book in dynamodb_books}
            
            verification_result['missing_books'] = list(s3_filenames - dynamodb_filenames)
            verification_result['extra_books'] = list(dynamodb_filenames - s3_filenames)
            
            logger.info(f"Verification complete: {verification_result['dynamodb_books_count']}/{verification_result['s3_books_count']} books migrated")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying migration: {e}")
            return {'error': str(e)}


def main():
    """Main migration function"""
    print("🚀 Starting S3 to DynamoDB Migration")
    print("=" * 50)
    
    migrator = S3ToDynamoDBMigrator()
    
    # Step 1: Create backup
    print("📦 Step 1: Creating backup...")
    backup_success = migrator.backup_existing_data()
    if not backup_success:
        print("❌ Backup failed, aborting migration")
        return
    
    # Step 2: Run migration
    print("🔄 Step 2: Running migration...")
    migration_result = migrator.migrate_all_books()
    
    if migration_result['success']:
        print(f"✅ Migration completed successfully!")
        print(f"   📚 Total books: {migration_result['total_books']}")
        print(f"   ✅ Migrated: {migration_result['migrated']}")
        print(f"   ❌ Failed: {migration_result['failed']}")
        
        if migration_result['errors']:
            print("   ⚠️  Errors:")
            for error in migration_result['errors']:
                print(f"      - {error}")
    else:
        print(f"❌ Migration failed: {migration_result.get('error', 'Unknown error')}")
        return
    
    # Step 3: Verify migration
    print("🔍 Step 3: Verifying migration...")
    verification = migrator.verify_migration()
    
    if verification.get('migration_successful'):
        print("✅ Migration verification passed!")
        print(f"   📊 S3 books: {verification['s3_books_count']}")
        print(f"   📊 DynamoDB books: {verification['dynamodb_books_count']}")
    else:
        print("⚠️  Migration verification failed!")
        if verification.get('missing_books'):
            print(f"   Missing books: {verification['missing_books']}")
        if verification.get('extra_books'):
            print(f"   Extra books: {verification['extra_books']}")
    
    print("=" * 50)
    print("🎉 Migration process completed!")


if __name__ == "__main__":
    main()

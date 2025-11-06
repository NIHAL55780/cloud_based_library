"""
Script to update book metadata in S3
Run this once to set genres for all your books
"""

import boto3
import os
from dotenv import load_dotenv
from config import Config

load_dotenv()

s3_client = boto3.client(
    's3',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN')
)

# Use the same bucket name from config
BUCKET_NAME = Config.S3_BUCKET_NAME

print(f"Using bucket: {BUCKET_NAME}")
print(f"Region: {os.getenv('AWS_REGION')}\n")

# Define genre mapping for your books
BOOK_GENRES = {
    'Persuasion by jane austen': 'Romance / Classic Literature',
    'persuasion': 'Romance / Classic Literature',
    'as_a_man_thinketh': 'Self-Help / Inspirational',
    'wingsoffire': 'Biography / Inspirational',
    'wings': 'Biography / Inspirational',
    'charllote': 'Romance / Gothic Fiction',
    'charlotte': 'Romance / Gothic Fiction',
    'jane eyre': 'Romance / Gothic Fiction',
    'power of positive': 'Self-Help / Motivational',
    'positive thinking': 'Self-Help / Motivational',
    'pride and prejudice': 'Romance / Classic Literature',
    'pride_and_prejudice': 'Romance / Classic Literature',
    'arundhati': 'Literary Fiction / Contemporary',
    'god of small things': 'Literary Fiction / Contemporary',
    'chariots': 'Mystery / Science Fiction',
    'ignited': 'Inspirational / Motivational',
    'ignited_minds': 'Inspirational / Motivational',
    'moonstone': 'Mystery / Detective Fiction',
    'abdul kalam': 'Biography / Inspirational',
    'james allen': 'Self-Help / Inspirational',
    'jane austen': 'Romance / Classic Literature',
    'wilkie collins': 'Mystery / Detective Fiction',
}

def update_book_metadata():
    """Update metadata for all books in S3"""
    try:
        # List all objects in bucket
        print(f"Fetching books from bucket: {BUCKET_NAME}...")
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in response:
            print("No books found in bucket")
            return
        
        print(f"Found {len(response['Contents'])} files\n")
        updated_count = 0
        
        for obj in response['Contents']:
            filename = obj['Key']
            
            # Skip non-book files
            if not filename.lower().endswith(('.pdf', '.epub', '.mobi')):
                print(f"Skipping non-book file: {filename}")
                continue
            
            # Extract book name without extension
            book_name = filename.rsplit('.', 1)[0]
            book_name_lower = book_name.lower()
            
            # Find matching genre
            genre = 'General'
            title = book_name
            author = 'Unknown'
            
            # Try to match with predefined genres (case-insensitive)
            for book_key, book_genre in BOOK_GENRES.items():
                if book_key.lower() in book_name_lower:
                    genre = book_genre
                    break
            
            # Extract title and author from filename
            if ' by ' in book_name:
                parts = book_name.split(' by ')
                title = parts[0].strip()
                author = parts[1].strip()
            elif '_by_' in book_name:
                parts = book_name.split('_by_')
                title = parts[0].strip().replace('_', ' ')
                author = parts[1].strip().replace('_', ' ')
            
            # Copy object with new metadata
            print(f"Updating: {filename}")
            print(f"  Title: {title}")
            print(f"  Author: {author}")
            print(f"  Genre: {genre}")
            
            try:
                s3_client.copy_object(
                    Bucket=BUCKET_NAME,
                    CopySource={'Bucket': BUCKET_NAME, 'Key': filename},
                    Key=filename,
                    Metadata={
                        'title': title,
                        'author': author,
                        'genre': genre,
                        'description': f'A captivating book by {author}.'
                    },
                    MetadataDirective='REPLACE',
                    ContentType='application/pdf'
                )
                
                updated_count += 1
                print(f"  ✓ Updated successfully\n")
            except Exception as copy_error:
                print(f"  ✗ Failed to update: {str(copy_error)}\n")
        
        print(f"\n✅ Successfully updated metadata for {updated_count} books!")
        
    except Exception as e:
        print(f"❌ Error updating metadata: {str(e)}")
        print(f"\nPlease check:")
        print(f"1. Bucket name in config.py: {BUCKET_NAME}")
        print(f"2. AWS credentials are valid")
        print(f"3. You have permission to access the bucket")

if __name__ == '__main__':
    print("Starting book metadata update...\n")
    update_book_metadata()
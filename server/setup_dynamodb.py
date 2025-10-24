#!/usr/bin/env python3
"""
Quick Setup Script for DynamoDB Integration
Run this to set up DynamoDB tables and migrate your existing data
"""

import sys
import os
import logging
from pathlib import Path

# Add the server directory to Python path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

from dynamodb_setup import DynamoDBManager
from migrate_to_dynamodb import S3ToDynamoDBMigrator

def setup_dynamodb():
    """Set up DynamoDB tables"""
    print("🔧 Setting up DynamoDB tables...")
    
    try:
        db_manager = DynamoDBManager()
        success = db_manager.create_tables()
        
        if success:
            print("✅ DynamoDB tables created successfully!")
            return True
        else:
            print("❌ Failed to create DynamoDB tables")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up DynamoDB: {e}")
        return False

def migrate_data():
    """Migrate existing S3 data to DynamoDB"""
    print("📦 Migrating data from S3 to DynamoDB...")
    
    try:
        migrator = S3ToDynamoDBMigrator()
        result = migrator.migrate_all_books()
        
        if result['success']:
            print(f"✅ Migration completed!")
            print(f"   📚 Total books: {result['total_books']}")
            print(f"   ✅ Migrated: {result['migrated']}")
            print(f"   ❌ Failed: {result['failed']}")
            return True
        else:
            print(f"❌ Migration failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Digital Library DynamoDB Setup")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path("server/.env")
    if not env_file.exists():
        print("⚠️  No .env file found. Please create one from env.example")
        print("   cp env.example .env")
        print("   Then edit .env with your AWS credentials")
        return
    
    # Step 1: Setup DynamoDB
    print("\n📋 Step 1: Creating DynamoDB tables...")
    if not setup_dynamodb():
        print("❌ Setup failed at table creation")
        return
    
    # Step 2: Migrate data
    print("\n📋 Step 2: Migrating existing data...")
    if not migrate_data():
        print("❌ Setup failed during migration")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Update your Flask app to use the new DynamoDB routes")
    print("2. Test the new endpoints")
    print("3. Update your frontend to use the enhanced metadata")
    
    print("\n🔗 New API endpoints available:")
    print("   GET /books - Get all books with rich metadata")
    print("   GET /books/search?q=query - Search books")
    print("   GET /books/<book_id> - Get specific book")
    print("   PUT /books/<book_id> - Update book metadata")
    print("   POST /bookmarks/<book_id> - Add bookmark")
    print("   POST /books/<book_id>/rate - Rate a book")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to verify connection to your BookMetaData table
"""

import boto3
from botocore.exceptions import ClientError
import json
from config import Config

def test_bookmetadata_connection():
    """Test connection to your BookMetaData table"""
    print("🔍 Testing BookMetaData Table Connection")
    print("=" * 50)
    
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=Config.DYNAMODB_REGION)
        table = dynamodb.Table(Config.DYNAMODB_BOOKS_TABLE)  # BookMetaData
        
        print(f"📋 Table Name: {Config.DYNAMODB_BOOKS_TABLE}")
        print(f"🌍 Region: {Config.DYNAMODB_REGION}")
        
        # Test 1: Get table info
        print("\n1. Getting table information...")
        try:
            table_info = table.meta.client.describe_table(TableName=Config.DYNAMODB_BOOKS_TABLE)
            print("✅ Table exists and is accessible")
            
            # Show table structure
            key_schema = table_info['Table']['KeySchema']
            print(f"   Primary Key: {key_schema}")
            
            # Show attributes
            attributes = table_info['Table']['AttributeDefinitions']
            print(f"   Attributes: {[attr['AttributeName'] for attr in attributes]}")
            
            # Show indexes if any
            gsi = table_info['Table'].get('GlobalSecondaryIndexes', [])
            if gsi:
                print(f"   Global Secondary Indexes: {[idx['IndexName'] for idx in gsi]}")
            else:
                print("   No Global Secondary Indexes found")
                
        except ClientError as e:
            print(f"❌ Error accessing table: {e}")
            return False
        
        # Test 2: Scan table to see what data exists
        print("\n2. Scanning table for existing data...")
        try:
            response = table.scan(Limit=5)  # Get first 5 items
            items = response.get('Items', [])
            
            if items:
                print(f"✅ Found {len(items)} items in table")
                print("\n   Sample item structure:")
                sample_item = items[0]
                for key, value in sample_item.items():
                    print(f"     {key}: {type(value).__name__} = {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                
                # Show all items
                print(f"\n   All items in table:")
                for i, item in enumerate(items, 1):
                    title = item.get('title', item.get('Title', 'Unknown'))
                    author = item.get('author', item.get('Author', 'Unknown'))
                    filename = item.get('filename', item.get('Filename', 'Unknown'))
                    print(f"     {i}. {title} by {author} ({filename})")
                    
            else:
                print("⚠️  No items found in table")
                
        except ClientError as e:
            print(f"❌ Error scanning table: {e}")
            return False
        
        # Test 3: Test getting a specific book by filename
        print("\n3. Testing book lookup by filename...")
        if items:
            # Try to get the first book by its filename
            first_item = items[0]
            filename = first_item.get('filename', first_item.get('Filename'))
            
            if filename:
                print(f"   Testing lookup for: {filename}")
                try:
                    # Try different methods to find the book
                    found_book = None
                    
                    # Method 1: Direct get_item if filename is primary key
                    try:
                        response = table.get_item(Key={'filename': filename})
                        found_book = response.get('Item')
                        if found_book:
                            print("   ✅ Found using direct get_item with filename as key")
                    except:
                        pass
                    
                    # Method 2: Scan with filter
                    if not found_book:
                        response = table.scan(
                            FilterExpression='filename = :filename',
                            ExpressionAttributeValues={':filename': filename}
                        )
                        scan_items = response.get('Items', [])
                        if scan_items:
                            found_book = scan_items[0]
                            print("   ✅ Found using scan with filename filter")
                    
                    if found_book:
                        print(f"   📖 Book found: {found_book.get('title', 'Unknown')}")
                    else:
                        print("   ❌ Book not found")
                        
                except Exception as e:
                    print(f"   ❌ Error in lookup: {e}")
            else:
                print("   ⚠️  No filename found in first item")
        else:
            print("   ⚠️  No items to test lookup with")
        
        print("\n" + "=" * 50)
        print("🎉 BookMetaData table test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_table_schema():
    """Show the current table schema"""
    print("\n📋 Current Table Schema:")
    print("-" * 30)
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=Config.DYNAMODB_REGION)
        table = dynamodb.Table(Config.DYNAMODB_BOOKS_TABLE)
        
        table_info = table.meta.client.describe_table(TableName=Config.DYNAMODB_BOOKS_TABLE)
        
        print(f"Table Name: {table_info['Table']['TableName']}")
        print(f"Status: {table_info['Table']['TableStatus']}")
        print(f"Item Count: {table_info['Table']['ItemCount']}")
        
        print("\nKey Schema:")
        for key in table_info['Table']['KeySchema']:
            print(f"  {key['AttributeName']}: {key['KeyType']}")
        
        print("\nAttributes:")
        for attr in table_info['Table']['AttributeDefinitions']:
            print(f"  {attr['AttributeName']}: {attr['AttributeType']}")
            
    except Exception as e:
        print(f"Error getting schema: {e}")

if __name__ == "__main__":
    show_table_schema()
    test_bookmetadata_connection()

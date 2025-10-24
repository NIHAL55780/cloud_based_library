#!/usr/bin/env python3
"""
Test script to verify DynamoDB queries work correctly
"""

from dynamodb_helper import SimpleDynamoDBHelper

def test_dynamodb_queries():
    """Test DynamoDB queries directly"""
    print("🔍 Testing DynamoDB Queries")
    print("=" * 50)
    
    try:
        db_helper = SimpleDynamoDBHelper()
        
        # Get all books first
        print("1. Getting all books from table...")
        all_books = db_helper.get_all_books()
        print(f"✅ Found {len(all_books)} books")
        
        if all_books:
            print("\n📖 Sample books:")
            for i, book in enumerate(all_books[:3]):
                print(f"  {i+1}. {book.get('Title', 'NO_TITLE')} by {book.get('Author', 'NO_AUTHOR')}")
        
        # Test specific queries
        print("\n2. Testing specific queries...")
        
        # Test 1: Search for "Charllote"
        print("\n🔍 Testing search for 'Charllote'...")
        result = db_helper.get_book_by_filename("Charllote.pdf")
        if result:
            print(f"✅ Found: {result.get('Title', 'Unknown')} by {result.get('Author', 'Unknown')}")
        else:
            print("❌ No match found")
        
        # Test 2: Search for "Jane Eyre"
        print("\n🔍 Testing search for 'Jane Eyre.pdf'...")
        result = db_helper.get_book_by_filename("Jane Eyre.pdf")
        if result:
            print(f"✅ Found: {result.get('Title', 'Unknown')} by {result.get('Author', 'Unknown')}")
        else:
            print("❌ No match found")
        
        # Test 3: Search for "Persuasion"
        print("\n🔍 Testing search for 'Persuasion.pdf'...")
        result = db_helper.get_book_by_filename("Persuasion.pdf")
        if result:
            print(f"✅ Found: {result.get('Title', 'Unknown')} by {result.get('Author', 'Unknown')}")
        else:
            print("❌ No match found")
        
        # Test 4: Manual scan test
        print("\n🔍 Testing manual scan for 'Charllote'...")
        try:
            response = db_helper.books_table.scan(
                FilterExpression='contains(Title, :title)',
                ExpressionAttributeValues={':title': 'Charllote'}
            )
            items = response.get('Items', [])
            print(f"✅ Manual scan found {len(items)} items")
            for item in items:
                print(f"   - {item.get('Title', 'Unknown')} by {item.get('Author', 'Unknown')}")
        except Exception as e:
            print(f"❌ Manual scan failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_dynamodb_queries()

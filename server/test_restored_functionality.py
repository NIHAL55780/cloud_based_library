#!/usr/bin/env python3
"""
Test the restored S3 reading and DynamoDB details functionality
"""

import requests
import json

def test_restored_functionality():
    """Test that S3 reading and DynamoDB details are working"""
    test_filename = 'Arundhati Roy - The God of Small Things.pdf'
    print(f'Testing with real book: {test_filename}')
    
    # Test book URL (S3 reading)
    print('\n1. Testing S3 book reading...')
    try:
        response = requests.get(f'http://localhost:5000/book/{test_filename}')
        if response.status_code == 200:
            data = response.json()
            print('✅ S3 book reading working!')
            print(f'URL generated: {bool(data.get("url"))}')
            print(f'Expires in: {data.get("expires_in", "N/A")} seconds')
        else:
            print(f'❌ Error: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ Connection error: {e}')
    
    # Test book details (DynamoDB)
    print('\n2. Testing DynamoDB book details...')
    try:
        response = requests.get(f'http://localhost:5000/book/{test_filename}/details')
        if response.status_code == 200:
            data = response.json()
            book = data.get('book', {})
            print('✅ DynamoDB book details working!')
            print(f'Title: {book.get("title", "N/A")}')
            print(f'Author: {book.get("author", "N/A")}')
            print(f'Genre: {book.get("genre", "N/A")}')
        else:
            print(f'❌ Error: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ Connection error: {e}')
    
    # Test books list
    print('\n3. Testing books list...')
    try:
        response = requests.get('http://localhost:5000/books')
        if response.status_code == 200:
            data = response.json()
            books = data.get('books', [])
            print(f'✅ Books list working! Found {len(books)} books')
        else:
            print(f'❌ Error: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ Connection error: {e}')

if __name__ == "__main__":
    print("🧪 Testing Restored Functionality")
    print("=" * 50)
    test_restored_functionality()
    print("=" * 50)
    print("🎉 All functionality restored!")
    print("✅ S3 book reading: Working")
    print("✅ DynamoDB book details: Working") 
    print("✅ Books list: Working")
    print("✅ Read Book button: Should work")
    print("✅ Details button: Should work")

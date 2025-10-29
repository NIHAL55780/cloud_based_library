#!/usr/bin/env python3
"""
Test the fixed book endpoints
"""

import requests
import json

def test_book_endpoints():
    """Test the book URL and details endpoints"""
    test_filename = 'Arundhati Roy - The God of Small Things.pdf'
    print(f'Testing book endpoints for: {test_filename}')
    
    # Test book URL endpoint
    print('\n1. Testing book URL endpoint...')
    try:
        response = requests.get(f'http://localhost:5000/book/{test_filename}')
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ SUCCESS! Book URL endpoint working')
            print(f'URL available: {bool(data.get("url"))}')
            print(f'Book title: {data.get("book_metadata", {}).get("title", "No title")}')
        else:
            print(f'❌ Error: {response.text}')
            
    except Exception as e:
        print(f'❌ Connection error: {e}')
    
    # Test book details endpoint
    print('\n2. Testing book details endpoint...')
    try:
        response = requests.get(f'http://localhost:5000/book/{test_filename}/details')
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ SUCCESS! Book details endpoint working')
            book = data.get('book', {})
            print(f'Book title: {book.get("title", "No title")}')
            print(f'Book author: {book.get("author", "No author")}')
        else:
            print(f'❌ Error: {response.text}')
            
    except Exception as e:
        print(f'❌ Connection error: {e}')

if __name__ == "__main__":
    print("🧪 Testing Fixed Book Endpoints")
    print("=" * 50)
    test_book_endpoints()
    print("=" * 50)

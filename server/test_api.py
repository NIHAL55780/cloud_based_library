#!/usr/bin/env python3
"""
Test the API endpoints to debug cover extraction
"""

import requests
import json

def test_api_endpoints():
    """Test the API endpoints to see what's happening"""
    try:
        # Test the books endpoint
        print("Testing books API...")
        response = requests.get('http://localhost:5000/books')
        print(f'Books API Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            books = data.get('books', [])
            print(f'Found {len(books)} books')
            
            if books:
                # Show first few books
                for i, book in enumerate(books[:3]):
                    print(f'  Book {i+1}: {book.get("title", "Unknown")} - {book.get("filename", "No filename")}')
                
                # Test cover extraction for the first book
                first_book = books[0]
                filename = first_book.get('filename')
                if filename:
                    print(f'\nTesting cover for: {filename}')
                    
                    # Test cover endpoint
                    cover_response = requests.get(f'http://localhost:5000/book/{filename}/cover')
                    print(f'Cover API Status: {cover_response.status_code}')
                    
                    if cover_response.status_code == 200:
                        cover_data = cover_response.json()
                        print(f'✅ Cover URL: {cover_data.get("cover_url")}')
                    else:
                        print(f'❌ Cover API Error: {cover_response.text}')
                else:
                    print('❌ No filename found in book data')
            else:
                print('No books found')
        else:
            print(f'❌ Books API Error: {response.text}')
            
    except requests.exceptions.ConnectionError:
        print('❌ Cannot connect to Flask server. Is it running?')
        print('   Start the server with: python app.py')
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    print("🧪 Testing API Endpoints")
    print("=" * 40)
    test_api_endpoints()
    print("=" * 40)
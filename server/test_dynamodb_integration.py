#!/usr/bin/env python3
"""
Test script to verify DynamoDB integration
"""

import requests
import json
import sys

def test_api_endpoints():
    """Test the new API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing DynamoDB Integration")
    print("=" * 40)
    
    # Test 1: Get all books
    print("\n1. Testing GET /books...")
    try:
        response = requests.get(f"{base_url}/books")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {data.get('count', 0)} books")
            if data.get('books'):
                print(f"   Sample book: {data['books'][0].get('title', 'Unknown')}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get book details (using first book's filename)
    print("\n2. Testing GET /book/<filename>/details...")
    try:
        # First get a list of books to find a filename
        response = requests.get(f"{base_url}/books")
        if response.status_code == 200:
            data = response.json()
            books = data.get('books', [])
            if books:
                filename = books[0].get('filename')
                if filename:
                    # Test the details endpoint
                    details_response = requests.get(f"{base_url}/book/{filename}/details")
                    if details_response.status_code == 200:
                        details_data = details_response.json()
                        book = details_data.get('book', {})
                        print(f"✅ Success: Retrieved details for '{book.get('title', 'Unknown')}'")
                        print(f"   Author: {book.get('author', 'Unknown')}")
                        print(f"   Genre: {book.get('genre', 'Unknown')}")
                        print(f"   File size: {book.get('s3_size', 0)} bytes")
                    else:
                        print(f"❌ Failed: {details_response.status_code} - {details_response.text}")
                else:
                    print("❌ No filename found in book data")
            else:
                print("❌ No books found")
        else:
            print(f"❌ Failed to get books: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Test with non-existent book
    print("\n3. Testing with non-existent book...")
    try:
        response = requests.get(f"{base_url}/book/non-existent-book.pdf/details")
        if response.status_code == 404:
            print("✅ Success: Correctly returned 404 for non-existent book")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 40)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    test_api_endpoints()

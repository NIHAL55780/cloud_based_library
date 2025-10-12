#!/usr/bin/env python3
"""
Test script for the Cloud-Based Digital Library API
Tests the main library endpoints to ensure they work correctly
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_BOOK_ID = None  # Will be set after creating a test book

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_all_books():
    """Test getting all books"""
    print("\nTesting GET /books endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/books")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_book_by_id(book_id):
    """Test getting a specific book by ID"""
    print(f"\nTesting GET /books/{book_id} endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/books/{book_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_upload_book():
    """Test uploading a book (without actual file)"""
    print("\nTesting POST /upload endpoint...")
    try:
        # Create a simple test file
        test_file_content = b"This is a test PDF content"
        test_filename = "test_book.pdf"
        
        # Create form data
        files = {
            'file': (test_filename, test_file_content, 'application/pdf')
        }
        
        data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'genre': 'Fiction',
            'description': 'This is a test book for API testing'
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            # Extract book ID from response for further testing
            response_data = response.json()
            if 'book_id' in response_data:
                global TEST_BOOK_ID
                TEST_BOOK_ID = response_data['book_id']
                print(f"Test book ID: {TEST_BOOK_ID}")
        
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_invalid_endpoints():
    """Test invalid endpoints to ensure proper error handling"""
    print("\nTesting invalid endpoints...")
    
    # Test non-existent book ID
    try:
        response = requests.get(f"{BASE_URL}/books/non-existent-id")
        print(f"GET /books/non-existent-id - Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test invalid upload (no file)
    try:
        response = requests.post(f"{BASE_URL}/upload")
        print(f"POST /upload (no file) - Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Cloud-Based Digital Library API Test Suite")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Server is not running or not accessible")
            print("Please start the Flask server with: python app.py")
            return
    except Exception as e:
        print("❌ Cannot connect to server")
        print("Please start the Flask server with: python app.py")
        print(f"Error: {e}")
        return
    
    print("✅ Server is running and accessible")
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Get All Books", test_get_all_books),
        ("Upload Book", test_upload_book),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Test getting the uploaded book if upload was successful
    if TEST_BOOK_ID:
        print(f"\n{'='*20} Get Book By ID {'='*20}")
        try:
            result = test_get_book_by_id(TEST_BOOK_ID)
            results.append(("Get Book By ID", result))
            print(f"✅ Get Book By ID: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ Get Book By ID: ERROR - {e}")
            results.append(("Get Book By ID", False))
    
    # Test invalid endpoints
    test_invalid_endpoints()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()

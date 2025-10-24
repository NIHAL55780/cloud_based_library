#!/usr/bin/env python3
"""
Test script to check which books work and which don't
"""

import requests
import json

def test_all_books():
    """Test all books to see which ones work"""
    print("🔍 Testing All Books")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Get all books from the table
    print("1. Getting all books from table...")
    try:
        response = requests.get(f"{base_url}/debug/books")
        if response.status_code == 200:
            data = response.json()
            books = data.get('books', [])
            print(f"✅ Found {len(books)} books in table")
        else:
            print(f"❌ Failed to get books: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting books: {e}")
        return
    
    # Test each book
    print("\n2. Testing each book...")
    working_books = []
    failing_books = []
    
    for i, book_info in enumerate(books[:5]):  # Test first 5 books
        print(f"\n📖 Testing book {i+1}: {book_info}")
        
        # Try different filename patterns for this book
        test_filenames = [
            f"{book_info}.pdf",  # Direct match
            f"{book_info} by Author.pdf",  # Author by Title
            f"Title by {book_info}.pdf",  # Title by Author
            f"{book_info} - Author.pdf",  # Title - Author
        ]
        
        for test_filename in test_filenames:
            try:
                # URL encode the filename
                import urllib.parse
                encoded_filename = urllib.parse.quote(test_filename)
                
                # Test the details endpoint
                response = requests.get(f"{base_url}/book/{encoded_filename}/details")
                if response.status_code == 200:
                    print(f"   ✅ Works with: {test_filename}")
                    working_books.append((book_info, test_filename))
                    break
                else:
                    print(f"   ❌ Failed with: {test_filename} ({response.status_code})")
            except Exception as e:
                print(f"   ❌ Error with {test_filename}: {e}")
        else:
            # If no filename worked
            failing_books.append(book_info)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   ✅ Working books: {len(working_books)}")
    print(f"   ❌ Failing books: {len(failing_books)}")
    
    if working_books:
        print(f"\n✅ Working books:")
        for book, filename in working_books:
            print(f"   - {book} (filename: {filename})")
    
    if failing_books:
        print(f"\n❌ Failing books:")
        for book in failing_books:
            print(f"   - {book}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_all_books()

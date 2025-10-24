#!/usr/bin/env python3
"""
Quick debug script to see what's in your table and test matching
"""

from dynamodb_helper import SimpleDynamoDBHelper
from urllib.parse import unquote

def quick_debug():
    print("🔍 Quick Debug - BookMetaData Table")
    print("=" * 50)
    
    try:
        db_helper = SimpleDynamoDBHelper()
        
        # Get all books
        books = db_helper.get_all_books()
        print(f"📚 Found {len(books)} books in table")
        
        if books:
            print("\n📖 First 5 books in your table:")
            for i, book in enumerate(books[:5]):
                bookid = book.get('BookID', 'NO_ID')
                title = book.get('Title', 'NO_TITLE')
                author = book.get('Author', 'NO_AUTHOR')
                print(f"  {i+1}. BookID: {bookid}")
                print(f"     Title: '{title}'")
                print(f"     Author: '{author}'")
                print()
        
        # Test filename parsing
        test_filename = "Charllote by Jane Eyre.pdf"
        print(f"🧪 Testing filename: '{test_filename}'")
        
        parsed = db_helper._parse_filename_to_title_author(test_filename)
        print(f"   Parsed Title: '{parsed['title']}'")
        print(f"   Parsed Author: '{parsed['author']}'")
        
        # Try to find matches
        print(f"\n🔍 Looking for matches...")
        matches = []
        for book in books:
            book_title = book.get('Title', '')
            book_author = book.get('Author', '')
            
            title_match = parsed['title'] and parsed['title'].lower() in book_title.lower()
            author_match = parsed['author'] and parsed['author'].lower() in book_author.lower()
            
            if title_match or author_match:
                matches.append({
                    'BookID': book.get('BookID'),
                    'Title': book_title,
                    'Author': book_author,
                    'title_match': title_match,
                    'author_match': author_match
                })
        
        print(f"✅ Found {len(matches)} potential matches:")
        for match in matches:
            print(f"   - {match['Title']} by {match['Author']}")
            print(f"     Title match: {match['title_match']}, Author match: {match['author_match']}")
        
        if not matches:
            print("❌ No matches found!")
            print("   This means the filename parsing isn't matching your table data.")
            print("   Let's see what we can match manually...")
            
            # Try manual matching
            print(f"\n🔧 Manual matching test:")
            for book in books[:3]:
                book_title = book.get('Title', '')
                book_author = book.get('Author', '')
                print(f"   Book: '{book_title}' by '{book_author}'")
                
                # Check if any part of the parsed data matches
                if parsed['title']:
                    title_contains = parsed['title'].lower() in book_title.lower()
                    print(f"     '{parsed['title']}' in title: {title_contains}")
                
                if parsed['author']:
                    author_contains = parsed['author'].lower() in book_author.lower()
                    print(f"     '{parsed['author']}' in author: {author_contains}")
                print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_debug()

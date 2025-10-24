#!/usr/bin/env python3
"""
Test script to verify filename parsing works with your table structure
"""

import re

def parse_filename_to_title_author(filename):
    """Parse filename to extract title and author"""
    # Remove file extension
    name_without_ext = filename.replace('.pdf', '').replace('.PDF', '')
    
    # Try different patterns
    patterns = [
        # "Author by Title" pattern
        r'(.+?)\s+by\s+(.+)',
        # "Title - Author" pattern  
        r'(.+?)\s+-\s+(.+)',
        # "Author - Title" pattern
        r'(.+?)\s+-\s+(.+)',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, name_without_ext, re.IGNORECASE)
        if match:
            part1, part2 = match.groups()
            # Heuristic: longer part is usually the title
            if len(part1.strip()) > len(part2.strip()):
                return {'title': part1.strip(), 'author': part2.strip()}
            else:
                return {'title': part2.strip(), 'author': part1.strip()}
    
    # If no pattern matches, treat the whole thing as title
    return {'title': name_without_ext.strip(), 'author': None}

def test_filename_parsing():
    """Test filename parsing with various patterns"""
    print("🔍 Testing Filename Parsing")
    print("=" * 50)
    
    test_cases = [
        "Charllote by Jane Eyre.pdf",
        "The Great Gatsby by F. Scott Fitzgerald.pdf", 
        "1984 by George Orwell.pdf",
        "Jane Austen - Pride and Prejudice.pdf",
        "Arundhati Roy - The God of Small Things.pdf",
        "Simple Title.pdf"
    ]
    
    for filename in test_cases:
        print(f"\nTesting: '{filename}'")
        result = parse_filename_to_title_author(filename)
        print(f"  Title: '{result['title']}'")
        print(f"  Author: '{result['author']}'")
        
        # Show what the DynamoDB query would look like
        if result['title'] and result['author']:
            print(f"  DynamoDB Filter: Title contains '{result['title']}' AND Author contains '{result['author']}'")
        elif result['title']:
            print(f"  DynamoDB Filter: Title contains '{result['title']}'")
        else:
            print(f"  DynamoDB Filter: No valid title/author extracted")

if __name__ == "__main__":
    test_filename_parsing()

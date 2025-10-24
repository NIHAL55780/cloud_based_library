#!/usr/bin/env python3
"""
Test script to check what filenames the frontend might be sending
"""

import requests
import json

def test_frontend_filenames():
    """Test common filenames that the frontend might send"""
    print("🔍 Testing Frontend Filenames")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Common filenames that the frontend might send
    test_filenames = [
        "Charllote by Jane Eyre.pdf",
        "Charllote.pdf", 
        "Jane Eyre.pdf",
        "Persuasion.pdf",
        "Persuasion by Jane Austen.pdf",
        "Ignited Minds.pdf",
        "Ignited Minds by A. P. J. Abdul Kalam.pdf",
        "The God of Small Things.pdf",
        "The God of Small Things by Arundhati Roy.pdf"
    ]
    
    print("Testing common frontend filenames...")
    
    for filename in test_filenames:
        print(f"\n📖 Testing: '{filename}'")
        
        try:
            # URL encode the filename
            import urllib.parse
            encoded_filename = urllib.parse.quote(filename)
            
            # Test the details endpoint
            response = requests.get(f"{base_url}/book/{encoded_filename}/details")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - Found book!")
                data = response.json()
                book = data.get('book', {})
                print(f"   📚 Book: {book.get('Title', 'Unknown')} by {book.get('Author', 'Unknown')}")
            else:
                print(f"   ❌ FAILED - {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('message', 'Unknown error')}")
                except:
                    print(f"   Response: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_frontend_filenames()

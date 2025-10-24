#!/usr/bin/env python3
"""
Test script to debug filename matching issues
"""

import requests
import json
from urllib.parse import unquote

def test_filename_matching():
    """Test filename matching between frontend and backend"""
    print("🔍 Testing Filename Matching")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Step 1: Get all filenames from the table
    print("\n1. Getting all filenames from BookMetaData table...")
    try:
        response = requests.get(f"{base_url}/debug/filenames")
        if response.status_code == 200:
            data = response.json()
            filenames = data.get('filenames', [])
            print(f"✅ Found {len(filenames)} filenames in table:")
            for i, filename in enumerate(filenames, 1):
                print(f"   {i}. \"{filename}\"")
        else:
            print(f"❌ Failed to get filenames: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting filenames: {e}")
        return
    
    # Step 2: Test with the first filename
    if filenames:
        test_filename = filenames[0]
        print(f"\n2. Testing with first filename: \"{test_filename}\"")
        
        # URL encode the filename
        import urllib.parse
        encoded_filename = urllib.parse.quote(test_filename)
        print(f"   URL encoded: \"{encoded_filename}\"")
        
        # Test the details endpoint
        try:
            response = requests.get(f"{base_url}/book/{encoded_filename}/details")
            if response.status_code == 200:
                data = response.json()
                book = data.get('book', {})
                print(f"✅ Success! Found book: {book.get('title', 'Unknown')}")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error testing details: {e}")
    
    # Step 3: Test with the problematic filename from the error
    print(f"\n3. Testing with problematic filename from error...")
    problematic_filename = "Charllote by Jane Eyre.pdf"
    print(f"   Testing: \"{problematic_filename}\"")
    
    try:
        encoded_problematic = urllib.parse.quote(problematic_filename)
        response = requests.get(f"{base_url}/book/{encoded_problematic}/details")
        if response.status_code == 200:
            data = response.json()
            book = data.get('book', {})
            print(f"✅ Success! Found book: {book.get('title', 'Unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Filename matching test completed!")

if __name__ == "__main__":
    test_filename_matching()

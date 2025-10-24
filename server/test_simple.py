#!/usr/bin/env python3
"""
Simple test to debug the exact issue
"""

import requests
import json

def test_backend():
    """Test the backend directly"""
    print("🔍 Testing Backend Directly")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Check if server is running
    print("1. Testing if server is running...")
    try:
        response = requests.get(f"{base_url}/debug/books")
        if response.status_code == 200:
            print("✅ Server is running")
            data = response.json()
            print(f"   Found {data.get('count', 0)} books")
        else:
            print(f"❌ Server error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure to run: python app.py")
        return
    
    # Test 2: Test filename parsing
    print("\n2. Testing filename parsing...")
    try:
        response = requests.get(f"{base_url}/debug/test-filename/Charllote%20by%20Jane%20Eyre.pdf")
        if response.status_code == 200:
            data = response.json()
            print("✅ Filename parsing works")
            print(f"   Parsed title: '{data.get('parsed_title')}'")
            print(f"   Parsed author: '{data.get('parsed_author')}'")
            print(f"   Found {len(data.get('matches', []))} matches")
            
            if data.get('matches'):
                print("   Matches:")
                for match in data['matches']:
                    print(f"     - {match['Title']} by {match['Author']}")
            else:
                print("   ❌ No matches found!")
        else:
            print(f"❌ Filename parsing failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing filename: {e}")
    
    # Test 3: Test the actual details endpoint
    print("\n3. Testing the actual details endpoint...")
    try:
        response = requests.get(f"{base_url}/book/Charllote%20by%20Jane%20Eyre.pdf/details")
        if response.status_code == 200:
            print("✅ Details endpoint works!")
            data = response.json()
            book = data.get('book', {})
            print(f"   Book: {book.get('Title', 'Unknown')} by {book.get('Author', 'Unknown')}")
        else:
            print(f"❌ Details endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing details: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_backend()

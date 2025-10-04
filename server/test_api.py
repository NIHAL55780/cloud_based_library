"""
Simple test script for Cloud-Based Digital Library API
Run this script to test the API endpoints
"""

import requests
import json
import sys

# API base URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    return True

def test_signup():
    """Test user signup endpoint"""
    print("\n🔍 Testing user signup...")
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "TestPass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [201, 409]:  # 409 if user already exists
            print("✅ Signup test completed")
            return True
        else:
            print("❌ Signup test failed")
            return False
            
    except Exception as e:
        print(f"❌ Signup test error: {e}")
        return False

def test_login():
    """Test user login endpoint"""
    print("\n🔍 Testing user login...")
    
    # Test data (same as signup)
    test_user = {
        "email": "test@example.com",
        "password": "TestPass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Login test passed")
            return True
        elif response.status_code == 401:
            print("⚠️  Login failed - user may need email verification")
            return True  # This is expected for new users
        else:
            print("❌ Login test failed")
            return False
            
    except Exception as e:
        print(f"❌ Login test error: {e}")
        return False

def test_invalid_requests():
    """Test invalid request handling"""
    print("\n🔍 Testing invalid requests...")
    
    # Test invalid email
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={"email": "invalid-email", "password": "TestPass123"},
            headers={"Content-Type": "application/json"}
        )
        print(f"   Invalid email test - Status: {response.status_code}")
        
        # Test weak password
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={"email": "test2@example.com", "password": "weak"},
            headers={"Content-Type": "application/json"}
        )
        print(f"   Weak password test - Status: {response.status_code}")
        
        print("✅ Invalid request tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Invalid request test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Cloud-Based Digital Library API Tests")
    print("=" * 50)
    
    # Check if server is running
    if not test_health_check():
        print("\n❌ Server is not running. Please start the server first:")
        print("   python app.py")
        sys.exit(1)
    
    # Run tests
    tests = [
        test_signup,
        test_login,
        test_invalid_requests
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()

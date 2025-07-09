#!/usr/bin/env python3
"""
Test script for the onboarding flow.
This script tests the complete user creation and onboarding process.
"""

import requests
import json
import sys
import os

# Add Backend to path
sys.path.append('./Backend')
from new_user_email import send_welcome_email

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your deployed URL
TEST_EMAIL = "test@example.com"
TEST_NAME = "Test User"
TEST_LANGUAGE = "spanish"

def test_user_creation():
    """Test creating a new user."""
    print("🧪 Testing user creation...")
    
    url = f"{BASE_URL}/api/users"
    data = {
        "email": TEST_EMAIL,
        "name": TEST_NAME,
        "language": TEST_LANGUAGE
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ User created successfully!")
            print(f"   User ID: {result['user_id']}")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ User creation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def test_token_verification(token):
    """Test token verification."""
    print(f"\n🧪 Testing token verification...")
    
    url = f"{BASE_URL}/api/verify-token/{token}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Token verified successfully!")
            print(f"   User: {result['user']['name']} ({result['user']['email']})")
            print(f"   Language: {result['user']['target_language']}")
            return result['user']
        else:
            print(f"❌ Token verification failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error verifying token: {e}")
        return None

def test_onboarding_completion(token, user_data):
    """Test completing onboarding."""
    print(f"\n🧪 Testing onboarding completion...")
    
    url = f"{BASE_URL}/api/complete-onboarding"
    data = {
        "token": token,
        "skill_level": 50,
        "learning_goal": "I want to become conversational in Spanish for travel and work.",
        "topics_of_interest": "Travel, food, business, culture, music"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Onboarding completed successfully!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Onboarding completion failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error completing onboarding: {e}")
        return False

def test_email_sending():
    """Test email sending functionality."""
    print(f"\n🧪 Testing email sending...")
    
    try:
        # Test with a sample token
        test_token = "test_token_12345"
        success = send_welcome_email(
            user_name=TEST_NAME,
            user_email=TEST_EMAIL,
            user_language=TEST_LANGUAGE,
            user_token=test_token
        )
        
        if success:
            print(f"✅ Email sending test completed!")
            print(f"   Check your SendGrid logs for the test email")
        else:
            print(f"❌ Email sending test failed!")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing email sending: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Bennie Onboarding Flow Tests")
    print("=" * 50)
    
    # Test 1: User Creation
    if not test_user_creation():
        print("\n❌ User creation test failed. Stopping tests.")
        return
    
    # Test 2: Email Sending
    test_email_sending()
    
    # Note: For a complete test, you would need to:
    # 1. Check your email for the actual token
    # 2. Use that token in the verification and completion tests
    # 3. Or create a test endpoint that returns the token
    
    print("\n" + "=" * 50)
    print("✅ Basic tests completed!")
    print("\n📝 Next steps:")
    print("1. Check your email for the welcome email")
    print("2. Extract the token from the email link")
    print("3. Use that token to test the verification and completion endpoints")
    print("4. Test the full onboarding flow in the browser")

if __name__ == "__main__":
    main() 
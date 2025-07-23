#!/usr/bin/env python3
"""
Test script to verify user creation endpoint.
"""

import os
import requests
import logging
from dotenv import load_dotenv
from supabase import create_client
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(verbose=True)  # Added verbose flag to see what's being loaded

# Debug environment variables (without showing values)
logger.info("Environment variables check:")
logger.info(f"SUPABASE_URL configured: {'SUPABASE_URL' in os.environ}")
logger.info(f"SUPABASE_KEY configured: {'SUPABASE_KEY' in os.environ}")

# Verify we can create a Supabase client
try:
    supabase = create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
    )
    logger.info("✅ Supabase client created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Supabase client: {e}")
    exit(1)

API_URL = "http://localhost:8000"  # Local development URL

def test_user_creation():
    """Test the user creation endpoint"""
    
    # Generate unique test email
    unique_id = str(uuid.uuid4())[:8]
    test_user = {
        "email": f"benniedevtest+{unique_id}@gmail.com",
        "name": f"Bennie_dev_test_{unique_id}",
        "language": "japanese"
    }
    
    try:
        # Create user
        logger.info(f"Testing user creation with data: {test_user}")
        response = requests.post(
            f"{API_URL}/api/users",
            json=test_user
        )
        
        # Log response
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.json()}")
        
        # Check response
        if response.status_code == 200:
            logger.info("✅ User creation successful!")
            result = response.json()
            
            # Verify response structure
            assert result["success"] == True, "Success flag should be True"
            assert "user_id" in result, "Response should contain user_id"
            assert result["user"]["email"] == test_user["email"], "Email should match"
            assert result["user"]["name"] == test_user["name"], "Name should match"
            assert result["user"]["target_language"] == test_user["language"], "Language should match"
            
            logger.info("✅ Response validation successful!")
            return True
            
        else:
            logger.error(f"❌ User creation failed with status code: {response.status_code}")
            logger.error(f"Error response: {response.json()}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    # Ensure the server is running
    try:
        health_check = requests.get(f"{API_URL}/health")
        if health_check.status_code != 200:
            logger.error("❌ Server is not running or health check failed")
            exit(1)
    except Exception as e:
        logger.error(f"❌ Could not connect to server: {e}")
        exit(1)
    
    # Run the test
    success = test_user_creation()
    
    if success:
        logger.info("✅ All tests passed!")
        exit(0)
    else:
        logger.error("❌ Tests failed!")
        exit(1) 
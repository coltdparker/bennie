#!/usr/bin/env python3
"""
Test script to verify the complete authentication flow.
This script tests:
1. User creation in auth.users
2. Automatic profile creation in public.users
3. Email history creation
4. User verification and onboarding
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import logging
import sys
from typing import Dict, Optional
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing required environment variables")
    sys.exit(1)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_test_user() -> Optional[Dict]:
    """Create a test user in auth.users."""
    try:
        # Generate unique email
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create user in auth.users
        auth_response = supabase.auth.admin.create_user({
            "email": test_email,
            "email_confirm": True,
            "user_metadata": {
                "name": "Test User",
                "target_language": "spanish",
                "proficiency_level": 1,
                "topics_of_interest": "travel, food",
                "learning_goal": "Become conversational",
                "motivation_goal": "Travel to Spain",
                "target_proficiency": 50,
                "email_schedule": {"frequency": "weekly"}
            }
        })
        
        if not auth_response or not auth_response.user:
            logger.error("Failed to create auth user")
            return None
        
        logger.info(f"✓ Created auth user: {test_email}")
        return {
            "auth_user_id": auth_response.user.id,
            "email": test_email
        }
        
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        return None

def verify_user_profile(auth_user_id: str) -> bool:
    """Verify user profile was created in public.users."""
    try:
        response = supabase.table("users").select("*").eq("auth_user_id", auth_user_id).execute()
        
        if not response.data:
            logger.error("User profile not created")
            return False
        
        profile = response.data[0]
        logger.info(f"✓ User profile created: {profile}")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying user profile: {e}")
        return False

def create_test_email(auth_user_id: str) -> bool:
    """Create a test email history entry."""
    try:
        response = supabase.table("email_history").insert({
            "auth_user_id": auth_user_id,
            "content": "This is a test email.",
            "is_from_bennie": True,
            "difficulty_level": 1
        }).execute()
        
        if not response.data:
            logger.error("Failed to create email history")
            return False
        
        logger.info("✓ Created test email history")
        return True
        
    except Exception as e:
        logger.error(f"Error creating test email: {e}")
        return False

def verify_relationships(auth_user_id: str) -> bool:
    """Verify relationships between tables."""
    try:
        # Get user profile
        profile_resp = supabase.table("users").select("*").eq("auth_user_id", auth_user_id).execute()
        if not profile_resp.data:
            logger.error("User profile not found")
            return False
        
        # Get email history
        email_resp = supabase.table("email_history").select("*").eq("auth_user_id", auth_user_id).execute()
        if not email_resp.data:
            logger.error("Email history not found")
            return False
        
        logger.info("✓ Verified table relationships")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying relationships: {e}")
        return False

def cleanup_test_user(auth_user_id: str) -> bool:
    """Clean up test user and related data."""
    try:
        # Delete auth user (should cascade to public.users and email_history)
        supabase.auth.admin.delete_user(auth_user_id)
        logger.info("✓ Cleaned up test user")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up test user: {e}")
        return False

def main():
    logger.info("Starting authentication flow test...")
    
    # Create test user
    user = create_test_user()
    if not user:
        logger.error("Test failed: Could not create test user")
        return False
    
    # Verify user profile creation
    if not verify_user_profile(user["auth_user_id"]):
        logger.error("Test failed: User profile not created")
        cleanup_test_user(user["auth_user_id"])
        return False
    
    # Create test email
    if not create_test_email(user["auth_user_id"]):
        logger.error("Test failed: Could not create test email")
        cleanup_test_user(user["auth_user_id"])
        return False
    
    # Verify relationships
    if not verify_relationships(user["auth_user_id"]):
        logger.error("Test failed: Invalid relationships")
        cleanup_test_user(user["auth_user_id"])
        return False
    
    # Clean up
    if not cleanup_test_user(user["auth_user_id"]):
        logger.error("Warning: Failed to clean up test user")
    
    logger.info("✓ All tests passed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
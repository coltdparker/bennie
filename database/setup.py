#!/usr/bin/env python3
"""
Database setup and testing script for Bennie.
This script helps verify Supabase connection and table structure.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def test_supabase_connection():
    """Test the Supabase connection and print configuration."""
    print("🔧 Testing Supabase Connection...")
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL not found in environment variables")
        return False
    
    if not SUPABASE_KEY:
        print("❌ SUPABASE_KEY not found in environment variables")
        return False
    
    print(f"✅ SUPABASE_URL: {SUPABASE_URL}")
    print(f"✅ SUPABASE_KEY: {SUPABASE_KEY[:6]}...")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client created successfully")
        return supabase
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return False

def test_table_exists(supabase: Client):
    """Test if the users table exists and has the correct structure."""
    print("\n📋 Testing users table...")
    
    try:
        # Try to select from users table
        response = supabase.table("users").select("count", count="exact").limit(1).execute()
        
        if response.error:
            print(f"❌ Error accessing users table: {response.error}")
            return False
        
        print("✅ Users table exists and is accessible")
        
        # Get table structure by selecting all columns
        structure_response = supabase.table("users").select("*").limit(1).execute()
        
        if structure_response.error:
            print(f"❌ Error getting table structure: {structure_response.error}")
            return False
        
        print("✅ Table structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing table: {e}")
        return False

def test_insert_user(supabase: Client):
    """Test inserting a user to verify permissions."""
    print("\n👤 Testing user insertion...")
    
    test_user = {
        "email": "test@example.com",
        "name": "Test User",
        "target_language": "spanish"
    }
    
    try:
        # First check if test user exists
        existing = supabase.table("users").select("id").eq("email", test_user["email"]).execute()
        
        if existing.data and len(existing.data) > 0:
            print("⚠️  Test user already exists, skipping insertion test")
            return True
        
        # Try to insert test user
        response = supabase.table("users").insert(test_user).execute()
        
        if response.error:
            print(f"❌ Error inserting test user: {response.error}")
            return False
        
        if not response.data or len(response.data) == 0:
            print("❌ No data returned from insert operation")
            return False
        
        user_id = response.data[0]["id"]
        print(f"✅ Test user inserted successfully with ID: {user_id}")
        
        # Clean up - delete test user
        delete_response = supabase.table("users").delete().eq("id", user_id).execute()
        
        if delete_response.error:
            print(f"⚠️  Warning: Could not delete test user: {delete_response.error}")
        else:
            print("✅ Test user cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing user insertion: {e}")
        return False

def print_setup_instructions():
    """Print instructions for setting up the database."""
    print("\n" + "="*60)
    print("📚 SUPABASE SETUP INSTRUCTIONS")
    print("="*60)
    print("""
1. Go to your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of database/schema.sql
4. Run the SQL script to create the users table
5. Verify the table was created in the Table Editor
6. Check that Row Level Security (RLS) is enabled
7. Verify the service role policies are in place

Environment Variables Required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_KEY: Your Supabase service role key (not anon key)

The service role key should have full access to the database.
The anon key is for client-side operations and has limited permissions.
    """)

def main():
    """Main function to run all tests."""
    print("🚀 Bennie Database Setup and Testing")
    print("="*40)
    
    # Test connection
    supabase = test_supabase_connection()
    if not supabase:
        print_setup_instructions()
        sys.exit(1)
    
    # Test table
    if not test_table_exists(supabase):
        print_setup_instructions()
        sys.exit(1)
    
    # Test insertion
    if not test_insert_user(supabase):
        print_setup_instructions()
        sys.exit(1)
    
    print("\n🎉 All tests passed! Your Supabase setup is working correctly.")
    print("You can now run the Bennie application.")

if __name__ == "__main__":
    main() 
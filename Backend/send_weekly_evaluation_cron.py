#!/usr/bin/env python3
"""
Weekly evaluation email cron job for Railway.
This script sends weekly evaluation emails to all active users.

Usage:
    python Backend/send_weekly_evaluation_cron.py

Set your SUPABASE_URL, SUPABASE_KEY, SENDGRID_API_KEY, and OPENAI_API_KEY in environment variables.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from Backend.send_weekly_evaluation_email import send_weekly_evaluation_email

def main():
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
        sys.exit(1)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🚀 Starting weekly evaluation email job...")
    
    try:
        # Get all active, verified users
        users_resp = supabase.table("users").select("email").eq("is_active", True).eq("is_verified", True).execute()
        
        if not users_resp.data:
            print("No active/verified users found for weekly evals.")
            return
        
        print(f"Found {len(users_resp.data)} users for weekly evaluations")
        
        success_count = 0
        error_count = 0
        
        for user in users_resp.data:
            email = user["email"]
            try:
                print(f"Sending weekly evaluation to {email}...")
                send_weekly_evaluation_email(email)
                success_count += 1
                print(f"✓ Weekly evaluation email sent to {email}")
            except Exception as e:
                error_count += 1
                print(f"✗ Failed to send weekly evaluation to {email}: {e}")
        
        print(f"\n📊 Weekly Evaluation Summary:")
        print(f"Total users: {len(users_resp.data)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {error_count}")
        
    except Exception as e:
        print(f"Weekly evaluation job failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
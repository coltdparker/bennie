#!/usr/bin/env python3
"""
Batch email sender for Bennie - for use with Railway cron jobs.
Sends up to 100 learning emails per run, starting from a given offset.

Usage:
    python send_batch_learning_emails.py [offset]

- offset: (optional) start index for batch (default 0)

Set your SUPABASE_URL, SUPABASE_KEY, SENDGRID_API_KEY, and OPENAI_API_KEY in .env
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from Backend.bennie_email_sender import send_language_learning_email

BATCH_SIZE = 100

def get_users_to_email(supabase, offset=0, limit=BATCH_SIZE):
    """
    Get active users from auth.users and public.users for batch emailing.
    Only returns users who have completed onboarding (have a profile in public.users).
    """
    # Get active users from public.users
    response = supabase.table("users").select(
        "auth_user_id"
    ).eq("is_active", True).range(offset, offset+limit-1).execute()
    
    if not response.data:
        return []
    
    # Get corresponding auth users
    auth_user_ids = [user["auth_user_id"] for user in response.data]
    auth_users = []
    
    # Fetch users in batches of 10 to avoid rate limits
    for i in range(0, len(auth_user_ids), 10):
        batch_ids = auth_user_ids[i:i+10]
        for auth_user_id in batch_ids:
            try:
                user = supabase.auth.admin.get_user(auth_user_id)
                if user:
                    auth_users.append({"email": user.email})
            except Exception as e:
                print(f"Error fetching auth user {auth_user_id}: {e}")
                continue
    
    return auth_users

def main():
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
        sys.exit(1)
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Parse offset from CLI
    offset = 0
    if len(sys.argv) > 1:
        try:
            offset = int(sys.argv[1])
        except Exception:
            print("Invalid offset argument, using 0.")
            offset = 0

    users = get_users_to_email(supabase, offset=offset, limit=BATCH_SIZE)
    print(f"Found {len(users)} users to email (offset {offset})")
    
    success_count = 0
    error_count = 0
    
    for user in users:
        try:
            print(f"Sending email to {user['email']}...")
            send_language_learning_email(user["email"])
            success_count += 1
            print(f"✓ Successfully sent to {user['email']}")
        except Exception as e:
            error_count += 1
            print(f"✗ Failed to send to {user['email']}: {e}")
    
    print(f"\n📊 Batch Summary:")
    print(f"Total users: {len(users)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")

if __name__ == "__main__":
    main() 
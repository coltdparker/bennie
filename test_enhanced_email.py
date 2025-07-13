#!/usr/bin/env python3
"""
Test script for the enhanced email functionality.
This script tests the new context-aware email generation system.
"""

import os
import sys
from dotenv import load_dotenv
from Backend.bennie_email_sender import (
    send_language_learning_email, 
    get_user_context, 
    analyze_topic_diversity,
    create_enhanced_prompt
)

def test_user_context():
    """Test fetching user context from database."""
    print("🔍 Testing user context fetching...")
    
    # Test with a known user email
    test_email = "coltdparker@gmail.com"  # Replace with a real user email from your database
    
    try:
        context = get_user_context(test_email)
        print("✅ User context fetched successfully:")
        print(f"   Name: {context['name']}")
        print(f"   Language: {context['target_language']}")
        print(f"   Level: {context['proficiency_level']}")
        print(f"   Interests: {context['topics_of_interest']}")
        print(f"   Learning Goal: {context['learning_goal']}")
        print(f"   Email History Count: {len(context['email_history'])}")
        return context
    except Exception as e:
        print(f"❌ Failed to fetch user context: {e}")
        return None

def test_topic_analysis(context):
    """Test topic diversity analysis."""
    print("\n🔍 Testing topic diversity analysis...")
    
    if not context:
        print("❌ No context available for testing")
        return
    
    try:
        recent_topics, should_use_new = analyze_topic_diversity(context['email_history'])
        print("✅ Topic analysis completed:")
        print(f"   Recent topics: {recent_topics}")
        print(f"   Should use new topic: {should_use_new}")
        return recent_topics, should_use_new
    except Exception as e:
        print(f"❌ Failed to analyze topics: {e}")
        return None, None

def test_prompt_creation(context, recent_topics, should_use_new):
    """Test enhanced prompt creation."""
    print("\n🔍 Testing enhanced prompt creation...")
    
    if not context:
        print("❌ No context available for testing")
        return
    
    try:
        prompt = create_enhanced_prompt(context, recent_topics or [], should_use_new or True)
        print("✅ Enhanced prompt created successfully")
        print(f"   Prompt length: {len(prompt)} characters")
        
        # Show a preview of the prompt
        print("\n📝 Prompt Preview (first 500 chars):")
        print("-" * 50)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print("-" * 50)
        
        return prompt
    except Exception as e:
        print(f"❌ Failed to create prompt: {e}")
        return None

def test_email_sending():
    """Test the complete email sending process."""
    print("\n🔍 Testing complete email sending...")
    
    # Test with a known user email
    test_email = "coltdparker@gmail.com"  # Replace with a real user email from your database
    
    try:
        print(f"Sending test email to {test_email}...")
        send_language_learning_email(test_email)
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def main():
    """Run all tests."""
    load_dotenv()
    
    print("🚀 Enhanced Email System Test")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'OPENAI_API_KEY', 'SENDGRID_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these in your .env file")
        return
    
    print("✅ Environment variables configured")
    
    # Test user context
    context = test_user_context()
    
    # Test topic analysis
    recent_topics, should_use_new = test_topic_analysis(context)
    
    # Test prompt creation
    prompt = test_prompt_creation(context, recent_topics, should_use_new)
    
    # Ask user if they want to test actual email sending
    print("\n" + "=" * 50)
    response = input("Do you want to test actual email sending? (y/N): ").lower().strip()
    
    if response == 'y':
        test_email_sending()
    else:
        print("Skipping email sending test")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main() 
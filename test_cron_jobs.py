#!/usr/bin/env python3
"""
Test script for Bennie cron jobs.
This script tests both the batch email sender and weekly evaluation sender.

Usage:
    python test_cron_jobs.py [batch|weekly|both]

Examples:
    python test_cron_jobs.py batch      # Test batch emails only
    python test_cron_jobs.py weekly     # Test weekly evaluations only
    python test_cron_jobs.py both       # Test both (default)
    python test_cron_jobs.py            # Test both (default)
"""

import sys
import os
from dotenv import load_dotenv

def test_batch_emails():
    """Test the batch email sender."""
    print("🧪 Testing Batch Email Sender...")
    print("=" * 50)
    
    try:
        from Backend.send_batch_learning_emails import main as batch_main
        batch_main()
        print("✅ Batch email test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Batch email test failed: {e}")
        return False

def test_weekly_evaluations():
    """Test the weekly evaluation sender."""
    print("\n🧪 Testing Weekly Evaluation Sender...")
    print("=" * 50)
    
    try:
        from Backend.send_weekly_evaluation_cron import main as weekly_main
        weekly_main()
        print("✅ Weekly evaluation test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Weekly evaluation test failed: {e}")
        return False

def test_dev_auto_eval():
    """Test the dev auto-evaluation endpoint."""
    print("\n🧪 Testing Dev Auto-Evaluation...")
    print("=" * 50)
    
    try:
        import httpx
        import os
        
        # Get the Railway URL from environment or use localhost
        railway_url = os.getenv("RAILWAY_URL", "http://localhost:8000")
        endpoint_url = f"{railway_url}/api/trigger-dev-auto-eval"
        
        print(f"Calling endpoint: {endpoint_url}")
        response = httpx.post(endpoint_url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Dev auto-eval test completed: {result}")
            return True
        else:
            print(f"❌ Dev auto-eval test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Dev auto-eval test failed: {e}")
        return False

def main():
    """Main test function."""
    load_dotenv()
    
    print("🚀 Bennie Cron Job Test Suite")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "SENDGRID_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment.")
        sys.exit(1)
    
    print("✅ Environment variables configured")
    
    # Parse command line arguments
    test_type = sys.argv[1].lower() if len(sys.argv) > 1 else "both"
    
    results = {}
    
    if test_type in ["batch", "both"]:
        results["batch"] = test_batch_emails()
    
    if test_type in ["weekly", "both"]:
        results["weekly"] = test_weekly_evaluations()
    
    if test_type in ["dev", "both"]:
        results["dev"] = test_dev_auto_eval()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Your cron jobs are ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
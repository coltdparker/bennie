#!/usr/bin/env python3
"""
Diagnostic script for Bennie's inbound email processing.
This script helps identify why SendGrid isn't receiving email replies.
"""

import os
import requests
import dns.resolver
import socket
from dotenv import load_dotenv

load_dotenv()

def check_mx_records(domain):
    """Check MX records for a domain."""
    print(f"\n🔍 Checking MX records for {domain}...")
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        print("✅ MX records found:")
        for mx in mx_records:
            print(f"   {mx.exchange} (priority: {mx.preference})")
        return True
    except Exception as e:
        print(f"❌ Error checking MX records: {e}")
        return False

def check_dns_resolution(domain):
    """Check if a domain resolves."""
    print(f"\n🔍 Checking DNS resolution for {domain}...")
    try:
        ip = socket.gethostbyname(domain)
        print(f"✅ {domain} resolves to {ip}")
        return True
    except Exception as e:
        print(f"❌ {domain} does not resolve: {e}")
        return False

def test_webhook_endpoint(base_url):
    """Test if the webhook endpoint is accessible."""
    print(f"\n🔍 Testing webhook endpoint...")
    try:
        response = requests.get(f"{base_url}/api/test-webhook", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Webhook endpoint is accessible")
            print(f"   Secret configured: {data.get('secret_configured', False)}")
            return True
        else:
            print(f"❌ Webhook endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach webhook endpoint: {e}")
        return False

def check_sendgrid_inbound_parse():
    """Check SendGrid Inbound Parse configuration."""
    print(f"\n🔍 Checking SendGrid Inbound Parse setup...")
    print("""
To configure SendGrid Inbound Parse:

1. Go to SendGrid Dashboard → Settings → Inbound Parse
2. Add a new webhook with these settings:
   - Domain: itsbennie.com
   - URL: https://your-railway-app.railway.app/api/sendgrid-inbound?secret=YOUR_SECRET
   - Check "POST the raw, full MIME message"
   - Check "Send Grid" (optional, for spam filtering)
   - Check "Send Raw" (recommended)

3. After adding the webhook, SendGrid will provide MX records to add to your DNS.
   These typically look like:
   - mx.sendgrid.net (priority 10)
   - mx2.sendgrid.net (priority 10)

4. Add these MX records to your DNS provider (Cloudflare, etc.)
""")

def check_environment_variables():
    """Check if required environment variables are set."""
    print(f"\n🔍 Checking environment variables...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY', 
        'SENDGRID_API_KEY',
        'SENDGRID_WEBHOOK_SECRET'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def test_email_flow():
    """Test the complete email flow."""
    print(f"\n🔍 Testing email flow...")
    print("""
To test the complete flow:

1. Create a test user in your database
2. Send an email from that user's email address to Bennie@itsbennie.com
3. Check SendGrid Activity Feed for inbound emails
4. Check your application logs for webhook calls
5. Check the email_history table for new entries

Common issues:
- MX records not propagated (can take 24-48 hours)
- Wrong webhook URL in SendGrid
- DNS provider blocking MX records
- Email being sent to wrong address
""")

def main():
    print("🚀 Bennie Inbound Email Diagnostic")
    print("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Check DNS resolution
    dns_ok = check_dns_resolution("itsbennie.com")
    
    # Check MX records
    mx_ok = check_mx_records("itsbennie.com")
    
    # Test webhook endpoint (if we can determine the URL)
    webhook_ok = False
    railway_url = os.getenv("RAILWAY_URL") or "https://your-app.railway.app"
    if railway_url != "https://your-app.railway.app":
        webhook_ok = test_webhook_endpoint(railway_url)
    else:
        print(f"\n⚠️  Cannot test webhook - set RAILWAY_URL environment variable")
    
    # Check SendGrid configuration
    check_sendgrid_inbound_parse()
    
    # Test email flow
    test_email_flow()
    
    # Summary
    print(f"\n📊 Diagnostic Summary")
    print("=" * 50)
    print(f"Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"DNS Resolution: {'✅' if dns_ok else '❌'}")
    print(f"MX Records: {'✅' if mx_ok else '❌'}")
    print(f"Webhook Endpoint: {'✅' if webhook_ok else '❌'}")
    
    if not mx_ok:
        print(f"\n🚨 CRITICAL ISSUE: MX records are not configured!")
        print("This is why SendGrid isn't receiving emails.")
        print("Follow the SendGrid Inbound Parse setup instructions above.")
    
    if not env_ok:
        print(f"\n⚠️  WARNING: Some environment variables are missing!")
        print("Check your Railway environment variables.")
    
    print(f"\n💡 Next Steps:")
    print("1. Configure SendGrid Inbound Parse webhook")
    print("2. Add MX records to your DNS")
    print("3. Wait for DNS propagation (24-48 hours)")
    print("4. Test with a real email")
    print("5. Check SendGrid Activity Feed and application logs")

if __name__ == "__main__":
    main() 
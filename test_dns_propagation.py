#!/usr/bin/env python3
"""
Test DNS propagation for itsbennie.com MX records
"""

import dns.resolver
import requests
import time

def check_mx_from_multiple_sources():
    """Check MX records from different DNS servers to test propagation."""
    
    # Different DNS servers to test from
    dns_servers = [
        "8.8.8.8",      # Google DNS
        "1.1.1.1",      # Cloudflare DNS
        "208.67.222.222", # OpenDNS
        "9.9.9.9",      # Quad9
    ]
    
    print("🌐 Testing MX record propagation from different DNS servers...")
    print("=" * 60)
    
    for server in dns_servers:
        try:
            # Create a resolver using this specific DNS server
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [server]
            resolver.timeout = 5
            resolver.lifetime = 5
            
            mx_records = resolver.resolve("itsbennie.com", "MX")
            
            print(f"✅ {server} (Google/Cloudflare/OpenDNS/Quad9):")
            for mx in mx_records:
                print(f"   {mx.exchange} (priority: {mx.preference})")
                
        except Exception as e:
            print(f"❌ {server}: {e}")
        
        print()

def check_sendgrid_inbound_parse_status():
    """Check if SendGrid Inbound Parse is properly configured."""
    print("🔍 SendGrid Inbound Parse Configuration Check")
    print("=" * 60)
    print("""
To verify SendGrid Inbound Parse is set up correctly:

1. Go to SendGrid Dashboard → Settings → Inbound Parse
2. Look for a webhook configured for 'itsbennie.com'
3. Verify the destination URL is correct:
   https://your-railway-app.railway.app/api/sendgrid-inbound?secret=YOUR_SECRET

4. Make sure these options are checked:
   ✅ POST the raw, full MIME message
   ✅ Send Raw (recommended)

5. Check the SendGrid Activity Feed:
   - Go to SendGrid Dashboard → Activity
   - Look for "Inbound Parse" events
   - Send a test email to Bennie@itsbennie.com
   - You should see an inbound parse event if it's working

If you don't see inbound parse events, the issue might be:
- SendGrid Inbound Parse webhook not configured
- Wrong webhook URL
- DNS still propagating
- Email being sent to wrong address
""")

def test_email_delivery():
    """Test email delivery to Bennie@itsbennie.com"""
    print("📧 Email Delivery Test")
    print("=" * 60)
    print("""
To test if emails are reaching SendGrid:

1. Send a test email to Bennie@itsbennie.com from an external email address
   (NOT from an @itsbennie.com address)

2. Check SendGrid Activity Feed:
   - Go to SendGrid Dashboard → Activity
   - Look for the email in the activity feed
   - If you see it, SendGrid is receiving emails
   - If you don't see it, emails are still going elsewhere

3. Check your Railway logs:
   - Look for webhook POST requests to /api/sendgrid-inbound
   - If you see them, the webhook is working
   - If not, SendGrid isn't calling your webhook

4. Check your database:
   - Look in the email_history table for new entries
   - If you see entries, everything is working!

Common issues:
- DNS propagation delay (can take 24-48 hours)
- Email client caching old DNS results
- SendGrid Inbound Parse not configured
- Wrong webhook URL in SendGrid
""")

def main():
    print("🚀 Bennie DNS Propagation & Email Delivery Test")
    print("=" * 60)
    
    check_mx_from_multiple_sources()
    check_sendgrid_inbound_parse_status()
    test_email_delivery()
    
    print("\n💡 Quick Fixes to Try:")
    print("1. Clear your browser DNS cache: chrome://net-internals/#dns")
    print("2. Try sending email from a different network/device")
    print("3. Wait 1-2 hours for DNS propagation")
    print("4. Check SendGrid Inbound Parse configuration")
    print("5. Verify webhook URL in SendGrid matches your Railway app")

if __name__ == "__main__":
    main() 
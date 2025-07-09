# Onboarding Flow Troubleshooting Guide

## Overview
This guide helps troubleshoot issues with the Bennie onboarding flow, from user signup to completing the onboarding process.

## Flow Overview
1. User signs up on homepage → User created in database with verification token
2. Welcome email sent with onboarding link containing token
3. User clicks link → Onboarding page loads and verifies token
4. User completes onboarding form → Data saved to database, token cleared

## Common Issues and Solutions

### 1. Email Link Not Working (DNS Error)

**Symptoms:**
- Email link shows `urlXXXX.itsbennie.com` instead of `itsbennie.com`
- Clicking link results in DNS resolution error
- Nothing appears in backend logs

**Root Cause:**
SendGrid click tracking is rewriting the links to a subdomain that's not properly configured.

**Solutions:**
- ✅ **Fixed**: Disabled click tracking in `new_user_email.py`
- Alternative: Configure DNS CNAME for the tracking subdomain
- Alternative: Use a different email service

**Code Location:**
```python
# Backend/new_user_email.py
message.tracking_settings = {
    "click_tracking": {
        "enable": False,
        "enable_text": False
    }
}
```

### 2. Invalid Token Error

**Symptoms:**
- Onboarding page shows "Invalid access token"
- Token verification fails with 404 error

**Possible Causes:**
- Token not generated during user creation
- Token expired or already used
- Database connection issues

**Solutions:**
- Check that `generate_verification_token()` is called during user creation
- Verify token is stored in database `verification_token` field
- Check Supabase connection and RLS policies

**Code Location:**
```python
# main.py - User creation
verification_token = generate_verification_token()
insert_data = {
    # ... other fields
    "verification_token": verification_token
}
```

### 3. User Already Verified Error

**Symptoms:**
- Onboarding page shows "You have already completed onboarding"
- Token verification returns 400 error

**Cause:**
User has already completed onboarding and the token was cleared.

**Solutions:**
- This is expected behavior for security
- User should contact support if they need to update their preferences
- Consider adding a "reset onboarding" feature

### 4. Onboarding Form Submission Fails

**Symptoms:**
- Form submission returns error
- User data not saved to database

**Possible Causes:**
- Invalid request format
- Database update fails
- Token validation fails

**Solutions:**
- Check browser console for JavaScript errors
- Verify API endpoint format matches frontend request
- Check Supabase logs for database errors

**Code Location:**
```javascript
// onboard.js
const response = await fetch('/api/complete-onboarding', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        token: userToken,
        skill_level: formData.skillLevel,
        learning_goal: formData.learningGoal,
        topics_of_interest: formData.topicsOfInterest
    })
});
```

### 5. Email Not Received

**Symptoms:**
- User created successfully but no email received
- SendGrid logs show delivery failure

**Possible Causes:**
- Missing or invalid SendGrid API key
- Email address is invalid
- SendGrid account issues

**Solutions:**
- Check `SENDGRID_API_KEY` environment variable
- Verify SendGrid account status
- Check SendGrid logs for delivery status
- Test with a different email address

## Testing the Flow

### Manual Testing
1. Create a new user via the homepage
2. Check email for welcome message with onboarding link
3. Click the link and verify it goes to onboarding page
4. Complete the onboarding form
5. Verify user data is updated in database

### Automated Testing
Run the test script:
```bash
python test_onboarding.py
```

### Database Verification
Check user record in Supabase:
```sql
SELECT id, email, name, target_language, verification_token, is_verified, proficiency_level, learning_goal, topics_of_interest
FROM users 
WHERE email = 'user@example.com';
```

## API Endpoints

### Create User
```
POST /api/users
{
    "email": "user@example.com",
    "name": "User Name",
    "language": "spanish"
}
```

### Verify Token
```
GET /api/verify-token/{token}
```

### Complete Onboarding
```
POST /api/complete-onboarding
{
    "token": "verification_token",
    "skill_level": 50,
    "learning_goal": "I want to become conversational...",
    "topics_of_interest": "Travel, food, business..."
}
```

## Environment Variables Required

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_key
SENDGRID_API_KEY=your_sendgrid_api_key
```

## Logs to Monitor

### Backend Logs
- User creation logs
- Token verification logs
- Onboarding completion logs
- Email sending logs

### Frontend Console
- Token validation errors
- API request/response errors
- Form submission errors

### SendGrid Logs
- Email delivery status
- Bounce/block reports
- Click tracking data (if enabled)

## Security Considerations

1. **Token Security**: Tokens are cryptographically secure and single-use
2. **Token Expiration**: Consider adding expiration timestamps
3. **Rate Limiting**: Consider adding rate limits to prevent abuse
4. **Input Validation**: All user inputs are validated on both frontend and backend

## Future Improvements

1. **Token Expiration**: Add expiration timestamps to tokens
2. **Resend Email**: Allow users to request new onboarding emails
3. **Progress Tracking**: Track onboarding completion rates
4. **Analytics**: Add analytics for onboarding flow optimization 
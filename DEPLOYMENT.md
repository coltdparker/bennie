# Bennie - Deployment Checklist

## Pre-Deployment Setup

### 1. Supabase Configuration

- [ ] Create Supabase project
- [ ] Run `database/schema.sql` in Supabase SQL Editor
- [ ] Verify `users` table exists with correct structure
- [ ] Confirm RLS policies are in place
- [ ] Copy project URL and service role key

### 2. Environment Variables

Set these in Railway environment variables:

- [ ] `SUPABASE_URL` = `https://your-project-id.supabase.co`
- [ ] `SUPABASE_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (service role key)
- [ ] `SENDGRID_API_KEY` = `SG.xxxxxxxxxxxxx...`
- [ ] `OPENAI_API_KEY` = `sk-xxxxxxxxxxxxx...`
- [ ] `DEBUG` = `False` (for production)

### 3. Email Service Setup

- [ ] Create SendGrid account
- [ ] Verify sender domain (`itsbennie.com`)
- [ ] Set up email templates
- [ ] Test email delivery

### 4. Domain Configuration

- [ ] Point domain to Railway deployment
- [ ] Update CORS settings in `main.py` if needed
- [ ] Test SSL certificate

## Deployment Steps

### 1. Railway Deployment

```bash
# Deploy to Railway
railway up
```

### 2. Verify Deployment

- [ ] Check Railway logs for errors
- [ ] Test health endpoint: `https://your-app.railway.app/health`
- [ ] Verify database connection
- [ ] Test user creation API

### 3. Database Testing

```bash
# Run database test script
python database/setup.py
```

Expected output:
```
🚀 Bennie Database Setup and Testing
========================================
🔧 Testing Supabase Connection...
✅ SUPABASE_URL: https://your-project-id.supabase.co
✅ SUPABASE_KEY: eyJhbG...
✅ Supabase client created successfully

📋 Testing users table...
✅ Users table exists and is accessible
✅ Table structure test passed

👤 Testing user insertion...
✅ Test user inserted successfully with ID: uuid-here
✅ Test user cleaned up successfully

🎉 All tests passed! Your Supabase setup is working correctly.
```

### 4. Frontend Testing

- [ ] Test landing page loads correctly
- [ ] Test email input validation
- [ ] Test language selection
- [ ] Test form submission
- [ ] Verify success message appears
- [ ] Check user appears in Supabase database

### 5. Email Testing

- [ ] Test welcome email sending
- [ ] Verify email content and styling
- [ ] Test onboarding link functionality

## Post-Deployment Monitoring

### 1. Log Monitoring

- [ ] Set up Railway log monitoring
- [ ] Monitor for errors in application logs
- [ ] Check Supabase logs for database issues

### 2. Performance Monitoring

- [ ] Monitor API response times
- [ ] Check database query performance
- [ ] Monitor email delivery rates

### 3. User Analytics

- [ ] Track user signups
- [ ] Monitor form completion rates
- [ ] Track email engagement

## Troubleshooting Common Issues

### Database Connection Issues

1. Check environment variables are set correctly
2. Verify Supabase project is active
3. Test with database setup script
4. Check Railway logs for connection errors

### Email Delivery Issues

1. Verify SendGrid API key is correct
2. Check sender domain verification
3. Test email templates
4. Monitor SendGrid delivery logs

### Frontend Issues

1. Check CORS configuration
2. Verify static files are being served
3. Test API endpoints directly
4. Check browser console for errors

## Security Checklist

- [ ] Environment variables are secure
- [ ] API keys are not exposed in code
- [ ] CORS is properly configured
- [ ] RLS policies are in place
- [ ] HTTPS is enabled
- [ ] No sensitive data in logs

## Backup and Recovery

- [ ] Set up database backups
- [ ] Document recovery procedures
- [ ] Test backup restoration
- [ ] Keep deployment configuration backed up

## Maintenance

### Regular Tasks

- [ ] Monitor application logs
- [ ] Check database performance
- [ ] Update dependencies
- [ ] Review security settings
- [ ] Backup user data

### Updates

- [ ] Test updates in staging environment
- [ ] Deploy during low-traffic periods
- [ ] Monitor for issues after updates
- [ ] Have rollback plan ready

## Support Resources

- [Railway Documentation](https://docs.railway.app/)
- [Supabase Documentation](https://supabase.com/docs)
- [SendGrid Documentation](https://sendgrid.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Emergency Contacts

- Railway Support: [Railway Discord](https://discord.gg/railway)
- Supabase Support: [Supabase Discord](https://discord.supabase.com/)
- SendGrid Support: [SendGrid Support](https://support.sendgrid.com/)

---

**Last Updated**: January 27, 2025
**Version**: 1.0.0 
# Bennie - Railway Cron Scheduling System

## Overview

Bennie now uses **Railway's built-in cron job system** instead of in-process schedulers for reliable, persistent scheduling that works with Railway's stateless container architecture.

## Why This Change Was Necessary

### The Problem with In-Process Schedulers on Railway

1. **Container Restarts**: Railway containers can restart at any time due to:
   - Deployments
   - Platform maintenance
   - Scaling events
   - Resource constraints

2. **Lost Jobs**: When a container restarts, the APScheduler process dies and all scheduled jobs are lost

3. **No Persistence**: APScheduler runs in-memory and doesn't persist job schedules across restarts

4. **Unreliable Timing**: Jobs scheduled for specific times may never run if the container restarts

### The Solution: Railway Cron Jobs

Railway's cron system:
- ✅ **Persistent**: Jobs survive container restarts
- ✅ **Reliable**: Railway guarantees job execution
- ✅ **Scalable**: Works with Railway's architecture
- ✅ **Timezone-aware**: Respects your configured timezone

## Current Cron Job Configuration

### 1. Batch Learning Emails (3x per week)
```json
{
  "batch-emails": {
    "schedule": "0 8 * * 1,3,5",
    "command": "python Backend/send_batch_learning_emails.py"
  }
}
```

**Schedule**: Monday, Wednesday, Friday at 8:00 AM Eastern Time
**Command**: Runs the batch email sender for all active users

### 2. Weekly Evaluation Emails
```json
{
  "weekly-evaluations": {
    "schedule": "0 9 * * 6",
    "command": "python Backend/send_weekly_evaluation_cron.py"
  }
}
```

**Schedule**: Saturday at 9:00 AM Eastern Time
**Command**: Sends weekly progress evaluations to all active users

## Cron Schedule Format

Railway uses standard cron syntax: `minute hour day month day-of-week`

| Field | Values | Example |
|-------|--------|---------|
| minute | 0-59 | `0` = top of hour |
| hour | 0-23 | `8` = 8 AM |
| day | 1-31 | `*` = every day |
| month | 1-12 | `*` = every month |
| day-of-week | 0-7 (0=Sunday) | `1,3,5` = Mon, Wed, Fri |

## Timezone Handling

- **Railway cron jobs run in UTC** by default
- **Our schedules are configured for Eastern Time**:
  - `0 8 * * 1,3,5` = 8:00 AM Eastern (13:00 UTC during DST, 12:00 UTC during EST)
  - `0 9 * * 6` = 9:00 AM Eastern (14:00 UTC during DST, 13:00 UTC during EST)

## Dev Auto-Evaluation

Since Railway cron doesn't support frequent intervals (like every 10 minutes), the dev auto-evaluation is now handled differently:

### Option 1: Manual Trigger (Current)
- **Endpoint**: `POST /api/trigger-dev-auto-eval`
- **Usage**: Call this endpoint manually or via external service
- **Function**: Checks instant_reply users and sends evaluations if they have 3+ replies since last eval

### Option 2: External Cron Service (Recommended for Production)
You can use an external service like:
- **GitHub Actions** (free, runs every 10 minutes)
- **Cron-job.org** (free tier available)
- **EasyCron** (paid service)

Example GitHub Actions workflow:
```yaml
name: Dev Auto-Eval
on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
jobs:
  trigger-eval:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Dev Auto-Eval
        run: |
          curl -X POST https://your-app.railway.app/api/trigger-dev-auto-eval
```

## Monitoring and Debugging

### 1. Check Cron Job Logs
Railway provides logs for cron job execution:
```bash
railway logs --service cron
```

### 2. Test Cron Jobs Manually
You can trigger cron jobs manually in Railway dashboard:
1. Go to your Railway project
2. Navigate to the "Cron" tab
3. Click "Run Now" for any job

### 3. Health Check Endpoint
The `/health` endpoint shows overall system status:
```bash
curl https://your-app.railway.app/health
```

### 4. Manual Testing
Test individual components:
```bash
# Test batch emails
python Backend/send_batch_learning_emails.py

# Test weekly evaluations
python Backend/send_weekly_evaluation_cron.py

# Test dev auto-eval
curl -X POST https://your-app.railway.app/api/trigger-dev-auto-eval
```

## Deployment Checklist

- [ ] Deploy updated code to Railway
- [ ] Verify cron jobs are configured in Railway dashboard
- [ ] Test cron jobs manually
- [ ] Monitor logs for successful execution
- [ ] Set up external service for dev auto-eval (if needed)

## Troubleshooting

### Cron Jobs Not Running
1. Check Railway cron configuration in dashboard
2. Verify schedule syntax is correct
3. Check logs for execution errors
4. Ensure environment variables are set

### Timezone Issues
1. Verify cron schedule accounts for UTC conversion
2. Check if DST changes affect timing
3. Consider using external service with timezone support

### Email Delivery Issues
1. Check SendGrid API key configuration
2. Verify sender domain verification
3. Monitor SendGrid delivery logs
4. Check application logs for errors

## Migration from APScheduler

### What Changed
- ❌ Removed `apscheduler` dependency
- ❌ Removed `start_scheduler()` function
- ❌ Removed in-process job scheduling
- ✅ Added Railway cron configuration
- ✅ Created standalone cron scripts
- ✅ Added manual trigger endpoint

### Benefits
- **Reliability**: Jobs survive container restarts
- **Simplicity**: No complex scheduler management
- **Scalability**: Works with Railway's architecture
- **Monitoring**: Better visibility into job execution

## Future Improvements

1. **Add cron job monitoring** with alerts
2. **Implement retry logic** for failed jobs
3. **Add job execution metrics** and analytics
4. **Consider timezone-aware scheduling** with external services
5. **Add job queuing** for high-volume scenarios

---

**Last Updated**: January 27, 2025
**Version**: 2.0.0 (Cron-based scheduling) 
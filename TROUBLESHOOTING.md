# Bennie - Troubleshooting Guide

## Supabase Database Integration Issues

### Problem: Users are not being saved to the database

When users submit the form on the landing page, the frontend shows success but no records appear in the Supabase database.

### Root Causes & Solutions

#### 1. Missing or Incorrect Database Schema

**Problem**: The `users` table doesn't exist or has incorrect structure.

**Solution**: 
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the schema from `database/schema.sql`:

```sql
-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    target_language TEXT NOT NULL,
    skill_level INTEGER DEFAULT 1,
    learning_goal TEXT,
    topics_of_interest TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    last_email_sent TIMESTAMP WITH TIME ZONE,
    email_count INTEGER DEFAULT 0
);
```

#### 2. Row Level Security (RLS) Issues

**Problem**: RLS is enabled but no policies allow the service role to insert data.

**Solution**: Create the necessary RLS policies:

```sql
-- Enable RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Allow service role to insert users
CREATE POLICY "Service role can insert users" ON public.users
    FOR INSERT TO service_role
    WITH CHECK (true);

-- Allow service role to select users
CREATE POLICY "Service role can select users" ON public.users
    FOR SELECT TO service_role
    USING (true);

-- Allow service role to update users
CREATE POLICY "Service role can update users" ON public.users
    FOR UPDATE TO service_role
    USING (true)
    WITH CHECK (true);
```

#### 3. Incorrect API Key

**Problem**: Using the wrong Supabase API key.

**Solution**: 
- Use the **service role key** (not the anon key) for backend operations
- The service role key has full database access
- The anon key is for client-side operations with limited permissions

**How to find the correct key**:
1. Go to Supabase Dashboard → Settings → API
2. Copy the "service_role" key (not "anon" key)
3. Set it as `SUPABASE_KEY` in your environment variables

#### 4. Environment Variables Not Set

**Problem**: Missing or incorrect environment variables.

**Solution**: Ensure these are set in Railway:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase service role key

**Format**:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 5. CORS Issues

**Problem**: Frontend can't reach the backend API.

**Solution**: Check CORS configuration in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://itsbennie.com", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Testing Your Setup

#### 1. Run the Database Test Script

```bash
python database/setup.py
```

This script will:
- Test Supabase connection
- Verify table structure
- Test user insertion
- Provide setup instructions if issues are found

#### 2. Test the Health Endpoint

Visit `/health` endpoint to check database connectivity:

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "bennie",
  "database": "connected",
  "timestamp": "2025-01-27T00:00:00Z"
}
```

#### 3. Test User Creation API

```bash
curl -X POST https://your-app.railway.app/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "language": "spanish"
  }'
```

Expected response:
```json
{
  "success": true,
  "user_id": "uuid-here",
  "message": "User created successfully",
  "user": {
    "email": "test@example.com",
    "name": "Test User",
    "target_language": "spanish"
  }
}
```

### Debugging Steps

#### 1. Check Railway Logs

```bash
railway logs
```

Look for:
- Environment variable errors
- Supabase connection errors
- Database operation errors

#### 2. Check Supabase Logs

1. Go to Supabase Dashboard → Logs
2. Look for failed requests or permission errors
3. Check the "API" tab for request/response details

#### 3. Test Locally

1. Create a `.env` file with your Supabase credentials
2. Run the application locally:
   ```bash
   python main.py
   ```
3. Test the API endpoints locally

#### 4. Verify Table Structure

In Supabase SQL Editor, run:

```sql
-- Check if table exists
SELECT EXISTS (
   SELECT FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name = 'users'
);

-- Check table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public';

-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'users';
```

### Common Error Messages

#### "relation 'users' does not exist"
- **Solution**: Run the schema.sql script in Supabase SQL Editor

#### "permission denied for table users"
- **Solution**: Check RLS policies and ensure service role key is used

#### "duplicate key value violates unique constraint"
- **Solution**: User already exists, this is expected behavior

#### "invalid input syntax for type uuid"
- **Solution**: Check that the id column is properly configured as UUID

### Prevention

1. **Always test locally first** before deploying
2. **Use the database test script** to verify setup
3. **Monitor logs** for early detection of issues
4. **Keep environment variables secure** and never commit them to version control
5. **Use proper error handling** in your code

### Getting Help

If you're still experiencing issues:

1. Check the Railway logs for detailed error messages
2. Verify your Supabase project settings
3. Test with the provided database setup script
4. Ensure you're using the correct API keys
5. Check that all environment variables are properly set

### Quick Fix Checklist

- [ ] Run `database/schema.sql` in Supabase SQL Editor
- [ ] Verify RLS policies are in place
- [ ] Use service role key (not anon key) for `SUPABASE_KEY`
- [ ] Set both `SUPABASE_URL` and `SUPABASE_KEY` in Railway
- [ ] Test with `python database/setup.py`
- [ ] Check `/health` endpoint returns "connected" for database
- [ ] Verify CORS settings include your domain 
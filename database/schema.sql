-- Bennie Database Schema
-- Run this in your Supabase SQL editor

-- Add indexes if not already present
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_target_language ON public.users(target_language);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON public.users(is_active);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Service role policies for users table
CREATE POLICY "Service role can insert users" ON public.users
    FOR INSERT TO service_role
    WITH CHECK (true);

CREATE POLICY "Service role can select users" ON public.users
    FOR SELECT TO service_role
    USING (true);

CREATE POLICY "Service role can update users" ON public.users
    FOR UPDATE TO service_role
    USING (true)
    WITH CHECK (true);

-- Optionally, add similar policies for email_history if you will access it from the backend
ALTER TABLE public.email_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role can insert email_history" ON public.email_history
    FOR INSERT TO service_role
    WITH CHECK (true);

CREATE POLICY "Service role can select email_history" ON public.email_history
    FOR SELECT TO service_role
    USING (true);

CREATE POLICY "Service role can update email_history" ON public.email_history
    FOR UPDATE TO service_role
    USING (true)
    WITH CHECK (true);

-- (Do NOT recreate the users table, since it already exists)
-- (Do NOT drop or alter columns unless you intend to migrate data) 
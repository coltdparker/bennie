-- Bennie Database Schema
-- Run this in your Supabase SQL editor

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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_target_language ON public.users(target_language);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON public.users(is_active);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create policy to allow service role to insert users
CREATE POLICY "Service role can insert users" ON public.users
    FOR INSERT TO service_role
    WITH CHECK (true);

-- Create policy to allow service role to select users
CREATE POLICY "Service role can select users" ON public.users
    FOR SELECT TO service_role
    USING (true);

-- Create policy to allow service role to update users
CREATE POLICY "Service role can update users" ON public.users
    FOR UPDATE TO service_role
    USING (true)
    WITH CHECK (true);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE public.users IS 'Stores user information for Bennie language learning app';
COMMENT ON COLUMN public.users.id IS 'Unique identifier for the user';
COMMENT ON COLUMN public.users.email IS 'User email address (unique)';
COMMENT ON COLUMN public.users.name IS 'User display name';
COMMENT ON COLUMN public.users.target_language IS 'Language the user wants to learn';
COMMENT ON COLUMN public.users.skill_level IS 'User skill level (1-100)';
COMMENT ON COLUMN public.users.learning_goal IS 'User learning goal description';
COMMENT ON COLUMN public.users.topics_of_interest IS 'Comma-separated list of topics of interest';
COMMENT ON COLUMN public.users.is_active IS 'Whether the user is active and receiving emails';
COMMENT ON COLUMN public.users.last_email_sent IS 'Timestamp of last email sent to user';
COMMENT ON COLUMN public.users.email_count IS 'Total number of emails sent to user'; 
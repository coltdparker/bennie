-- Bennie Database Schema
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email text not null,
    name text not null,
    target_language text not null,
    proficiency_level integer null default 10,
    topics_of_interest text[] null default array[]::text[],
    learning_goal text null,
    motivation_goal text null,
    target_proficiency integer null default 20,  -- Default to basic level (20)
    current_level text DEFAULT 'Beginner',
    current_skill_rating text null,
    email_schedule jsonb null,
    is_active boolean null default true,
    instant_reply boolean null default false,
    created_at timestamp with time zone not null default TIMEZONE('utc', NOW()),
    updated_at timestamp with time zone not null default TIMEZONE('utc', NOW()),
    last_login timestamp with time zone null
) TABLESPACE pg_default;

-- Create email_history table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS public.email_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content text null,
    is_from_bennie boolean not null,
    difficulty_level integer null,
    created_at timestamp with time zone not null default TIMEZONE('utc', NOW()),
    is_evaluation boolean not null default false -- Marks if this is an evaluation email
) TABLESPACE pg_default;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON public.users(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_users_target_language ON public.users(target_language);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON public.users(is_active);
CREATE INDEX IF NOT EXISTS idx_email_history_auth_user_id ON public.email_history(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_email_history_created_at ON public.email_history(created_at);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_history ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users table policies
CREATE POLICY "Users can read own data" ON public.users
    FOR SELECT
    USING (auth.uid() = auth_user_id);

CREATE POLICY "Users can update own data" ON public.users
    FOR UPDATE
    USING (auth.uid() = auth_user_id);

CREATE POLICY "Service role has full access to users" ON public.users
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- Email history policies
CREATE POLICY "Users can read own email history" ON public.email_history
    FOR SELECT
    USING (auth.uid() = auth_user_id);

CREATE POLICY "Service role has full access to email history" ON public.email_history
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger to users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to handle new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (
        auth_user_id,
        email,
        name,
        target_language
    )
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
        COALESCE(NEW.raw_user_meta_data->>'target_language', 'english')
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for new auth users
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user(); 
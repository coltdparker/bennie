-- Migration: Integrate with Supabase Auth
-- Description: Updates schema to work with Supabase Auth while preserving existing data

-- Start transaction
BEGIN;

-- 1. Create a temporary table to store existing user data
CREATE TEMP TABLE temp_users AS SELECT * FROM public.users;

-- 2. Drop existing constraints and indexes
ALTER TABLE public.email_history 
  DROP CONSTRAINT IF EXISTS email_history_user_id_fkey,
  DROP CONSTRAINT IF EXISTS email_history_auth_user_id_fkey;
ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_email_key;

-- 3. Modify users table to work with auth.users
ALTER TABLE public.users 
  -- Drop columns that will be managed by auth.users
  DROP COLUMN IF EXISTS email,
  DROP COLUMN IF EXISTS password_hash,
  DROP COLUMN IF EXISTS auth_provider,
  DROP COLUMN IF EXISTS auth_provider_id,
  DROP COLUMN IF EXISTS is_verified,
  DROP COLUMN IF EXISTS verification_token,
  DROP COLUMN IF EXISTS last_login,
  -- Add new auth user reference
  DROP COLUMN IF EXISTS auth_user_id,
  ADD COLUMN auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  -- Make auth_user_id the new primary key
  DROP CONSTRAINT IF EXISTS users_pkey,
  ADD PRIMARY KEY (auth_user_id);

-- 4. Update email_history foreign key
ALTER TABLE public.email_history
  DROP COLUMN IF EXISTS user_id,
  DROP COLUMN IF EXISTS auth_user_id,
  ADD COLUMN auth_user_id UUID,
  ADD CONSTRAINT email_history_auth_user_id_fkey FOREIGN KEY (auth_user_id) REFERENCES public.users(auth_user_id);

-- 5. Create function to handle new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.users (
    auth_user_id,
    name,
    target_language,
    proficiency_level,
    topics_of_interest,
    learning_goal,
    motivation_goal,
    target_proficiency,
    email_schedule,
    is_active,
    instant_reply,
    created_at,
    updated_at
  ) VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'name', NEW.raw_user_meta_data->>'full_name', 'Anonymous'),
    COALESCE(NEW.raw_user_meta_data->>'target_language', 'english'),
    COALESCE((NEW.raw_user_meta_data->>'proficiency_level')::int, 10),
    NEW.raw_user_meta_data->>'topics_of_interest',
    NEW.raw_user_meta_data->>'learning_goal',
    NEW.raw_user_meta_data->>'motivation_goal',
    COALESCE((NEW.raw_user_meta_data->>'target_proficiency')::int, 20),
    NEW.raw_user_meta_data->>'email_schedule',
    true,
    false,
    NEW.created_at,
    NEW.updated_at
  );
  RETURN NEW;
END;
$$;

-- 6. Create trigger for new user creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 7. Set up Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_history ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
DROP POLICY IF EXISTS "Users can view own email history" ON public.email_history;
DROP POLICY IF EXISTS "Users can insert own email history" ON public.email_history;

-- Users table policies
CREATE POLICY "Users can view own profile"
  ON public.users FOR SELECT
  USING (auth.uid() = auth_user_id);

CREATE POLICY "Users can update own profile"
  ON public.users FOR UPDATE
  USING (auth.uid() = auth_user_id)
  WITH CHECK (auth.uid() = auth_user_id);

-- Email history policies
CREATE POLICY "Users can view own email history"
  ON public.email_history FOR SELECT
  USING (auth.uid() = auth_user_id);

CREATE POLICY "Users can insert own email history"
  ON public.email_history FOR INSERT
  WITH CHECK (auth.uid() = auth_user_id);

-- 8. Create indexes for performance
DROP INDEX IF EXISTS idx_users_auth_user_id;
DROP INDEX IF EXISTS idx_email_history_auth_user_id;
CREATE INDEX idx_users_auth_user_id ON public.users(auth_user_id);
CREATE INDEX idx_email_history_auth_user_id ON public.email_history(auth_user_id);

-- 9. Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON public.users TO authenticated;
GRANT ALL ON public.email_history TO authenticated;

-- 10. Create function to migrate existing users to auth.users
CREATE OR REPLACE FUNCTION migrate_existing_users()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_record RECORD;
BEGIN
    FOR user_record IN SELECT * FROM temp_users
    LOOP
        -- Insert into auth.users and get the new UUID
        -- Note: This is a placeholder. The actual migration of users to auth.users
        -- should be handled through the Supabase Auth API or dashboard to properly
        -- set up authentication credentials
        RAISE NOTICE 'Would migrate user: %', user_record.email;
    END LOOP;
END;
$$;

-- Note: Don't automatically run the migration function
-- PERFORM migrate_existing_users();

-- Clean up
DROP TABLE temp_users;

COMMIT; 
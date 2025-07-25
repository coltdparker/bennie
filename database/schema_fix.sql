-- Drop existing tables and start fresh
DROP TABLE IF EXISTS public.email_history;
DROP TABLE IF EXISTS public.users;

-- Recreate users table with correct structure
CREATE TABLE public.users (
    auth_user_id uuid NOT NULL,
    name text NOT NULL,
    target_language text NOT NULL,
    proficiency_level integer NOT NULL DEFAULT 1,
    topics_of_interest text NOT NULL DEFAULT ''::text,
    learning_goal text,  -- Nullable because it's set during onboarding
    motivation_goal text,  -- Nullable because it's set during onboarding
    target_proficiency integer NOT NULL DEFAULT 50,
    email_schedule jsonb,
    is_active boolean NOT NULL DEFAULT true,
    instant_reply boolean NOT NULL DEFAULT false,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone,
    CONSTRAINT users_pkey PRIMARY KEY (auth_user_id),
    CONSTRAINT users_auth_user_id_fkey FOREIGN KEY (auth_user_id)
        REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Recreate email_history table with correct structure
CREATE TABLE public.email_history (
    id bigint GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    auth_user_id uuid NOT NULL,  -- Changed to NOT NULL
    content text NOT NULL,  -- Changed to NOT NULL
    is_from_bennie boolean NOT NULL,
    difficulty_level integer NOT NULL,  -- Changed to NOT NULL since it's important for tracking
    is_evaluation boolean NOT NULL DEFAULT false,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT email_history_pkey PRIMARY KEY (id),
    CONSTRAINT email_history_auth_user_id_fkey FOREIGN KEY (auth_user_id)
        REFERENCES public.users(auth_user_id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_users_target_language ON public.users USING btree (target_language);
CREATE INDEX idx_users_created_at ON public.users USING btree (created_at);
CREATE INDEX idx_users_is_active ON public.users USING btree (is_active);
CREATE INDEX idx_users_auth_user_id ON public.users USING btree (auth_user_id);
CREATE INDEX idx_email_history_auth_user_id ON public.email_history USING btree (auth_user_id);
CREATE INDEX idx_email_history_created_at ON public.email_history USING btree (created_at);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_history ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = auth_user_id);

CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = auth_user_id)
    WITH CHECK (auth.uid() = auth_user_id);

CREATE POLICY "Users can view own email history"
    ON public.email_history FOR SELECT
    USING (auth.uid() = auth_user_id);

CREATE POLICY "Users can insert own email history"
    ON public.email_history FOR INSERT
    WITH CHECK (auth.uid() = auth_user_id);

-- Create trigger function for new users
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
        NEW.id,  -- auth.users.id becomes our auth_user_id
        COALESCE(NEW.raw_user_meta_data->>'name', NEW.raw_user_meta_data->>'full_name', 'Anonymous'),
        COALESCE(NEW.raw_user_meta_data->>'target_language', 'english'),
        COALESCE((NEW.raw_user_meta_data->>'proficiency_level')::int, 1),
        COALESCE(NEW.raw_user_meta_data->>'topics_of_interest', ''),
        NEW.raw_user_meta_data->>'learning_goal',
        NEW.raw_user_meta_data->>'motivation_goal',
        COALESCE((NEW.raw_user_meta_data->>'target_proficiency')::int, 50),
        COALESCE(NEW.raw_user_meta_data->'email_schedule', '{"frequency": "weekly"}'::jsonb),  -- Fixed JSONB handling
        true,
        false,
        NEW.created_at,
        NEW.updated_at
    );
    RETURN NEW;
END;
$$;

-- Create trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON public.users TO authenticated;
GRANT ALL ON public.email_history TO authenticated; 
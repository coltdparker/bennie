-- Test script to create a user with all required data
-- This script simulates both the auth.users creation and the trigger-based public.users creation

-- Start transaction
BEGIN;

-- 1. Create user in auth.users with metadata
DO $$
DECLARE
    new_user_id uuid;
    test_email text := 'coltdparker@gmail.com';
    test_name text := 'Test User';
BEGIN
    -- Insert into auth.users
    INSERT INTO auth.users (
        instance_id,
        id,
        aud,
        role,
        email,
        encrypted_password,
        email_confirmed_at,
        created_at,
        updated_at,
        raw_user_meta_data
    )
    VALUES (
        '00000000-0000-0000-0000-000000000000'::uuid, -- instance_id
        gen_random_uuid(),                            -- id
        'authenticated',                              -- aud
        'authenticated',                              -- role
        test_email,                                  -- email
        '1234567890',                                -- encrypted_password (dummy value)
        now(),                                       -- email_confirmed_at
        now(),                                       -- created_at
        now(),                                       -- updated_at
        jsonb_build_object(                          -- raw_user_meta_data
            'name', test_name,
            'target_language', 'spanish',
            'proficiency_level', 20,
            'topics_of_interest', 'travel, food, culture',
            'learning_goal', 'Become conversational in Spanish',
            'motivation_goal', 'I want to travel to Spain and communicate with locals',
            'target_proficiency', 60,
            'email_schedule', jsonb_build_object(     -- Properly structured JSONB for email_schedule
                'frequency', 'weekly',
                'preferred_days', ARRAY['monday', 'wednesday', 'friday'],
                'preferred_time', '10:00'
            )
        )
    )
    RETURNING id INTO new_user_id;

    -- Verify user was created in public.users via trigger
    IF NOT EXISTS (
        SELECT 1 
        FROM public.users 
        WHERE auth_user_id = new_user_id
    ) THEN
        RAISE EXCEPTION 'Failed to create user in public.users table';
    END IF;

    -- Test creating an email history entry
    INSERT INTO public.email_history (
        auth_user_id,
        content,
        is_from_bennie,
        difficulty_level,
        is_evaluation
    ) VALUES (
        new_user_id,
        'Hola! This is a test email to verify the relationship between users and email_history.',
        true,
        20,
        false
    );

    -- Output success message with user details
    RAISE NOTICE 'Test user created successfully:';
    RAISE NOTICE 'User ID: %', new_user_id;
    RAISE NOTICE 'Email: %', test_email;
    RAISE NOTICE 'Name: %', test_name;

END $$;

-- 2. Verify the setup
SELECT 
    u.email as auth_email,
    pu.name as public_name,
    pu.target_language,
    pu.proficiency_level,
    pu.target_proficiency,
    pu.email_schedule,  -- Added to verify JSONB data
    eh.id as latest_email_id,
    eh.content as latest_email
FROM 
    auth.users u
    JOIN public.users pu ON u.id = pu.auth_user_id
    LEFT JOIN public.email_history eh ON pu.auth_user_id = eh.auth_user_id
WHERE 
    u.email = 'coltdparker@gmail.com'
ORDER BY 
    eh.created_at DESC
LIMIT 1;

COMMIT; 
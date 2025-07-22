-- Test script for user creation and relationships

-- 1. First, let's create a function to simulate auth.users insertion
-- (This is for testing only - in production, Supabase handles this)
CREATE OR REPLACE FUNCTION test_create_auth_user(
    test_email TEXT,
    test_name TEXT,
    test_language TEXT
) RETURNS uuid AS $$
DECLARE
    new_user_id uuid;
BEGIN
    -- Insert into auth.users (simplified for testing)
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
        '00000000-0000-0000-0000-000000000000'::uuid,  -- instance_id
        gen_random_uuid(),  -- id
        'authenticated',    -- aud
        'authenticated',    -- role
        test_email,        -- email
        '**********',      -- encrypted_password (dummy value)
        now(),             -- email_confirmed_at
        now(),             -- created_at
        now(),             -- updated_at
        jsonb_build_object(  -- raw_user_meta_data
            'name', test_name,
            'target_language', test_language
        )
    )
    RETURNING id INTO new_user_id;

    RETURN new_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Test user creation
DO $$
DECLARE
    test_user_id uuid;
    users_count int;
    email_content text := 'Test email content';
BEGIN
    -- Create test user
    test_user_id := test_create_auth_user(
        'test@example.com',
        'Test User',
        'spanish'
    );

    -- Verify user was created in public.users
    SELECT COUNT(*) INTO users_count
    FROM public.users
    WHERE auth_user_id = test_user_id;

    ASSERT users_count = 1, 
        'Expected one user record in public.users';

    -- Test email history relationship
    INSERT INTO public.email_history (
        content,
        is_from_bennie,
        difficulty_level,
        auth_user_id
    ) VALUES (
        email_content,
        true,
        10,
        test_user_id
    );

    -- Verify email was created
    ASSERT EXISTS (
        SELECT 1 
        FROM public.email_history 
        WHERE auth_user_id = test_user_id
        AND content = email_content
    ), 'Expected email history record to be created';

    -- Clean up test data
    DELETE FROM public.email_history WHERE auth_user_id = test_user_id;
    DELETE FROM public.users WHERE auth_user_id = test_user_id;
    DELETE FROM auth.users WHERE id = test_user_id;

    RAISE NOTICE 'All tests passed successfully!';
END;
$$;

-- 3. View results
SELECT 'auth.users' as table_name, COUNT(*) as count FROM auth.users
UNION ALL
SELECT 'public.users' as table_name, COUNT(*) as count FROM public.users
UNION ALL
SELECT 'public.email_history' as table_name, COUNT(*) as count FROM public.email_history; 
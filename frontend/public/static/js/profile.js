import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
import getSupabaseConfig from './config.js';

async function initializeProfile() {
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const content = document.getElementById('profile-content');

    try {
        // Initialize Supabase client
        const config = await getSupabaseConfig();
        const supabase = createClient(config.url, config.anonKey);

        // Get current session
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError || !session) {
            throw new Error('Please sign in to view your profile');
        }

        // Fetch user profile data
        const { data: profile, error: profileError } = await supabase
            .from('users')
            .select('*')
            .eq('auth_user_id', session.user.id)
            .single();

        if (profileError) {
            throw profileError;
        }

        // Update UI with user data
        document.getElementById('user-name').textContent = profile.full_name || session.user.user_metadata?.full_name || 'Not set';
        document.getElementById('user-email').textContent = session.user.email;
        document.getElementById('user-level').textContent = profile.current_level || 'Beginner';
        document.getElementById('target-proficiency').textContent = profile.target_proficiency || 'Not set';
        document.getElementById('skill-rating').textContent = profile.current_skill_rating || 'Not assessed';
        document.getElementById('user-motivation').textContent = profile.motivation || 'Not set';
        document.getElementById('user-interests').textContent = profile.interests?.join(', ') || 'Not set';

        // Show content
        loading.style.display = 'none';
        content.style.display = 'block';

    } catch (err) {
        console.error('Profile loading error:', err);
        loading.style.display = 'none';
        error.textContent = err.message;
        error.style.display = 'block';

        // If not authenticated, redirect to sign in
        if (err.message.includes('sign in')) {
            setTimeout(() => {
                window.location.href = '/signin';
            }, 2000);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeProfile); 
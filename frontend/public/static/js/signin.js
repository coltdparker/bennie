import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
import getSupabaseConfig from './config.js';

let supabaseClient = null;

async function initializeSupabase() {
    try {
        const config = await getSupabaseConfig();
        console.log('Supabase config loaded:', { url: config.url, hasKey: !!config.anonKey });
        supabaseClient = createClient(config.url, config.anonKey);
        return supabaseClient;
    } catch (error) {
        console.error('Failed to initialize Supabase:', error);
        throw error;
    }
}

async function setupGoogleSignIn() {
    const googleSignInButton = document.getElementById('googleSignIn');
    if (!googleSignInButton) {
        console.error('Google sign-in button not found');
        return;
    }

    const errorDisplay = document.createElement('div');
    errorDisplay.className = 'error-message';
    document.querySelector('.oauth-buttons').after(errorDisplay);

    // Helper function to show error message
    const showError = (message, isWarning = false) => {
        console.error('Error:', message);
        errorDisplay.textContent = message;
        errorDisplay.style.display = 'block';
        errorDisplay.style.backgroundColor = isWarning ? 'rgba(251, 191, 36, 0.1)' : 'rgba(239, 68, 68, 0.1)';
        errorDisplay.style.color = isWarning ? '#D97706' : 'var(--error-red)';
    };

    // Helper function to hide error message
    const hideError = () => {
        errorDisplay.style.display = 'none';
    };

    // Helper function to set loading state
    const setLoading = (isLoading) => {
        const buttons = document.querySelectorAll('.oauth-button:not([disabled])');
        buttons.forEach(button => {
            button.disabled = isLoading;
            if (button.id === 'googleSignIn') {
                button.querySelector('span').textContent = isLoading ? 'Signing in...' : 'Sign in with Google';
            }
        });
    };

    // Handle Google Sign In
    googleSignInButton.addEventListener('click', async () => {
        try {
            hideError();
            setLoading(true);

            if (!supabaseClient) {
                throw new Error('Supabase client not initialized');
            }

            // Generate and store state parameter
            const state = btoa(crypto.randomUUID());
            sessionStorage.setItem('oauth_state', state);

            console.log('Initiating Google sign-in...');
            const { data, error } = await supabaseClient.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: `${window.location.origin}/auth/callback`,
                    queryParams: {
                        access_type: 'offline',
                        prompt: 'consent',
                    }
                }
            });

            if (error) {
                console.error('OAuth error:', error);
                throw error;
            }

            if (data?.url) {
                console.log('Redirecting to:', data.url);
                window.location.href = data.url;
            } else {
                throw new Error('No redirect URL received from Supabase');
            }

        } catch (error) {
            console.error('Google sign-in error:', error);
            
            // Handle specific error cases
            if (error.message?.includes('popup_closed_by_user')) {
                showError('Sign-in was cancelled. Please try again.', true);
            } else if (error.message?.includes('configuration')) {
                showError('Authentication service is not properly configured. Please try again later.');
            } else if (error.message?.includes('network')) {
                showError('Network error. Please check your internet connection and try again.');
            } else if (error.message?.includes('redirect_url')) {
                showError('Invalid redirect URL. Please contact support.');
            } else {
                showError(`Failed to initialize sign-in: ${error.message}`);
            }
            
            setLoading(false);
        }
    });
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('Initializing Supabase...');
        await initializeSupabase();
        console.log('Setting up Google Sign In...');
        await setupGoogleSignIn();
        
        // Check for error in URL
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        const errorDescription = urlParams.get('error_description');
        
        if (error) {
            console.error('OAuth error in URL:', { error, description: errorDescription });
            const errorDisplay = document.createElement('div');
            errorDisplay.className = 'error-message';
            errorDisplay.textContent = errorDescription || error;
            document.querySelector('.oauth-buttons').after(errorDisplay);
        }
    } catch (error) {
        console.error('Initialization error:', error);
        const errorDisplay = document.createElement('div');
        errorDisplay.className = 'error-message';
        errorDisplay.textContent = 'Failed to initialize authentication. Please try again later.';
        document.querySelector('.oauth-buttons').after(errorDisplay);
    }
}); 
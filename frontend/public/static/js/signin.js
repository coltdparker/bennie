import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
import getSupabaseConfig from './config.js';

let supabaseClient = null;

async function initializeSupabase() {
    try {
        const config = await getSupabaseConfig();
        console.log('Supabase config loaded:', { url: config.url, hasKey: !!config.anonKey });
        supabaseClient = createClient(config.url, config.anonKey);
        
        // Check if we already have a session
        const { data: { session }, error: sessionError } = await supabaseClient.auth.getSession();
        if (session) {
            console.log('Existing session found, redirecting to profile...');
            window.location.href = '/profile';
            return;
        }
        
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

            // Get the current URL for the redirect
            const redirectUrl = new URL('/profile', window.location.origin).href;
            console.log('Initiating Google sign-in with redirect URL:', redirectUrl);

            const { data, error } = await supabaseClient.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: redirectUrl,
                    queryParams: {
                        state: state,
                        access_type: 'offline',
                        prompt: 'consent'
                    }
                }
            });

            if (error) {
                console.error('OAuth error:', error);
                throw error;
            }

            console.log('Sign-in initiated:', data);

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

// Handle OAuth redirect result
async function handleRedirect() {
    const hash = window.location.hash;
    if (!hash) return;

    try {
        console.log('Processing OAuth redirect...');
        
        // Check for error in redirect
        const params = new URLSearchParams(hash.substring(1));
        const errorParam = params.get('error');
        const errorDescription = params.get('error_description');
        
        if (errorParam) {
            console.error('OAuth redirect error:', errorParam, errorDescription);
            throw new Error(errorDescription || errorParam);
        }

        // Verify state parameter
        const state = params.get('state');
        const storedState = sessionStorage.getItem('oauth_state');
        
        if (state !== storedState) {
            console.error('State mismatch:', { received: state, stored: storedState });
            throw new Error('Invalid authentication state. Please try again.');
        }

        // Clear stored state
        sessionStorage.removeItem('oauth_state');

        // Get the session
        const { data: { session }, error } = await supabaseClient.auth.getSession();
        
        if (error) {
            console.error('Session error:', error);
            throw error;
        }
        
        if (!session) {
            console.error('No session established');
            throw new Error('Failed to establish session');
        }

        console.log('Authentication successful, redirecting to profile...');
        window.location.href = '/profile';

    } catch (error) {
        console.error('OAuth redirect error:', error);
        const errorDisplay = document.createElement('div');
        errorDisplay.className = 'error-message';
        errorDisplay.textContent = `Authentication failed: ${error.message}`;
        document.querySelector('.oauth-buttons').after(errorDisplay);
    }
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('Initializing Supabase...');
        await initializeSupabase();
        console.log('Setting up Google Sign In...');
        await setupGoogleSignIn();
        
        // Handle any redirect result
        await handleRedirect();
    } catch (error) {
        console.error('Initialization error:', error);
        const errorDisplay = document.createElement('div');
        errorDisplay.className = 'error-message';
        errorDisplay.textContent = 'Failed to initialize authentication. Please try again later.';
        document.querySelector('.oauth-buttons').after(errorDisplay);
    }
}); 
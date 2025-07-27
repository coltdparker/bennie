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

async function handleAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');
    const errorDescription = urlParams.get('error_description');
    
    if (error) {
        console.error('OAuth error in URL:', { error, description: errorDescription });
        showError(errorDescription || error);
        // Clean up URL
        window.history.replaceState({}, document.title, '/signin');
        return;
    }
    
    if (code) {
        console.log('Found authorization code, creating session...');
        try {
            // Exchange the code for a session
            const { data, error: sessionError } = await supabaseClient.auth.exchangeCodeForSession(code);
            
            if (sessionError) {
                console.error('Session creation error:', sessionError);
                throw sessionError;
            }
            
            if (data.session) {
                console.log('Session created successfully, redirecting to profile...');
                window.location.href = '/profile';
                return;
            } else {
                throw new Error('No session created');
            }
        } catch (error) {
            console.error('Error creating session from code:', error);
            showError('Failed to complete sign-in. Please try again.');
            // Clean up URL
            window.history.replaceState({}, document.title, '/signin');
        }
    }
}

function showError(message) {
    // Create or find error display element
    let errorDisplay = document.querySelector('.error-message');
    if (!errorDisplay) {
        errorDisplay = document.createElement('div');
        errorDisplay.className = 'error-message';
        errorDisplay.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
        errorDisplay.style.color = 'var(--error-red)';
        errorDisplay.style.padding = '10px';
        errorDisplay.style.borderRadius = '5px';
        errorDisplay.style.marginTop = '10px';
        document.querySelector('.oauth-buttons').after(errorDisplay);
    }
    
    errorDisplay.textContent = message;
    errorDisplay.style.display = 'block';
}

async function setupGoogleSignIn() {
    const googleSignInButton = document.getElementById('googleSignIn');
    if (!googleSignInButton) {
        console.error('Google sign-in button not found');
        return;
    }

    // Helper function to hide error message
    const hideError = () => {
        const errorDisplay = document.querySelector('.error-message');
        if (errorDisplay) {
            errorDisplay.style.display = 'none';
        }
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
                showError('Sign-in was cancelled. Please try again.');
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
        
        // Handle OAuth callback if code is present
        await handleAuthCallback();
        
    } catch (error) {
        console.error('Initialization error:', error);
        showError('Failed to initialize authentication. Please try again later.');
    }
}); 
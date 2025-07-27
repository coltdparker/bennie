import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
import getSupabaseConfig from './config.js';

let supabaseClient = null;

// Debug logging helper
function debugLog(section, message, data = null) {
    const logMessage = `[${section}] ${message}`;
    if (data) {
        console.log(logMessage, data);
    } else {
        console.log(logMessage);
    }
}

async function initializeSupabase() {
    try {
        debugLog('Supabase Init', 'Starting Supabase initialization...');
        const config = await getSupabaseConfig();
        debugLog('Supabase Config', 'Configuration loaded:', {
            hasUrl: !!config.url,
            hasKey: !!config.anonKey,
            urlDomain: config.url ? new URL(config.url).hostname : null
        });

        supabaseClient = createClient(config.url, config.anonKey);
        debugLog('Supabase Client', 'Client created successfully');
        
        // Check if we already have a session
        const { data: { session }, error: sessionError } = await supabaseClient.auth.getSession();
        debugLog('Session Check', 'Current session state:', {
            hasSession: !!session,
            error: sessionError
        });

        if (session) {
            debugLog('Session', 'Existing session found, redirecting to profile...');
            window.location.href = '/profile';
            return;
        }
        
        return supabaseClient;
    } catch (error) {
        debugLog('Supabase Init Error', 'Failed to initialize:', error);
        throw error;
    }
}

async function setupGoogleSignIn() {
    debugLog('Google Setup', 'Setting up Google Sign In...');
    const googleSignInButton = document.getElementById('googleSignIn');
    if (!googleSignInButton) {
        debugLog('Google Setup Error', 'Google sign-in button not found in DOM');
        return;
    }

    const errorDisplay = document.createElement('div');
    errorDisplay.className = 'error-message';
    document.querySelector('.oauth-buttons').after(errorDisplay);

    // Helper function to show error message
    const showError = (message, isWarning = false) => {
        debugLog('Error Display', `Showing ${isWarning ? 'warning' : 'error'}: ${message}`);
        errorDisplay.textContent = message;
        errorDisplay.style.display = 'block';
        errorDisplay.style.backgroundColor = isWarning ? 'rgba(251, 191, 36, 0.1)' : 'rgba(239, 68, 68, 0.1)';
        errorDisplay.style.color = isWarning ? '#D97706' : 'var(--error-red)';
    };

    // Helper function to hide error message
    const hideError = () => {
        debugLog('Error Display', 'Hiding error message');
        errorDisplay.style.display = 'none';
    };

    // Helper function to set loading state
    const setLoading = (isLoading) => {
        debugLog('UI State', `Setting loading state: ${isLoading}`);
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
            debugLog('Google Auth', 'Starting Google sign-in process...');
            hideError();
            setLoading(true);

            if (!supabaseClient) {
                throw new Error('Supabase client not initialized');
            }

            // Generate and store state parameter
            const state = btoa(crypto.randomUUID());
            sessionStorage.setItem('oauth_state', state);
            debugLog('OAuth State', 'Generated state parameter:', { state });

            // Get the current URL for the redirect
            const supabaseCallbackUrl = `${window.location.origin}/auth/callback`;
            debugLog('OAuth Config', 'Configured redirect URL:', { supabaseCallbackUrl });

            debugLog('Supabase Auth', 'Calling signInWithOAuth...');
            const { data, error } = await supabaseClient.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: supabaseCallbackUrl,
                    queryParams: {
                        state: state,
                        access_type: 'offline',
                        prompt: 'consent',
                        hd: 'gmail.com' // Optional: restrict to Gmail domains
                    },
                    skipBrowserRedirect: false // Ensure browser handles redirect
                }
            });

            if (error) {
                debugLog('OAuth Error', 'Error during OAuth initialization:', error);
                throw error;
            }

            debugLog('OAuth Success', 'Sign-in initiated successfully:', data);

        } catch (error) {
            debugLog('OAuth Error', 'Failed to complete OAuth flow:', error);
            
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

    debugLog('Google Setup', 'Google Sign In setup completed');
}

// Handle OAuth redirect result
async function handleRedirect() {
    const hash = window.location.hash;
    if (!hash) {
        debugLog('Redirect', 'No hash parameters found');
        return;
    }

    try {
        debugLog('Redirect', 'Processing OAuth redirect with hash:', hash);
        
        // Check for error in redirect
        const params = new URLSearchParams(hash.substring(1));
        const errorParam = params.get('error');
        const errorDescription = params.get('error_description');
        
        if (errorParam) {
            debugLog('Redirect Error', 'Error in OAuth redirect:', {
                error: errorParam,
                description: errorDescription
            });
            throw new Error(errorDescription || errorParam);
        }

        // Verify state parameter
        const state = params.get('state');
        const storedState = sessionStorage.getItem('oauth_state');
        debugLog('State Verification', 'Checking state parameter:', {
            received: state,
            stored: storedState,
            matches: state === storedState
        });
        
        if (state !== storedState) {
            throw new Error('Invalid authentication state. Please try again.');
        }

        // Clear stored state
        sessionStorage.removeItem('oauth_state');
        debugLog('State Cleanup', 'Cleared stored state');

        // Get the session
        debugLog('Session', 'Fetching session...');
        const { data: { session }, error } = await supabaseClient.auth.getSession();
        
        if (error) {
            debugLog('Session Error', 'Failed to get session:', error);
            throw error;
        }
        
        if (!session) {
            debugLog('Session Error', 'No session established');
            throw new Error('Failed to establish session');
        }

        debugLog('Auth Success', 'Authentication successful, redirecting to profile...');
        window.location.href = '/profile';

    } catch (error) {
        debugLog('Redirect Error', 'Failed to handle redirect:', error);
        const errorDisplay = document.createElement('div');
        errorDisplay.className = 'error-message';
        errorDisplay.textContent = `Authentication failed: ${error.message}`;
        document.querySelector('.oauth-buttons').after(errorDisplay);
    }
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    debugLog('Init', 'Starting application initialization...');
    try {
        await initializeSupabase();
        await setupGoogleSignIn();
        await handleRedirect();
        debugLog('Init', 'Application initialization completed');
    } catch (error) {
        debugLog('Init Error', 'Failed to initialize application:', error);
        const errorDisplay = document.createElement('div');
        errorDisplay.className = 'error-message';
        errorDisplay.textContent = 'Failed to initialize authentication. Please try again later.';
        document.querySelector('.oauth-buttons').after(errorDisplay);
    }
}); 
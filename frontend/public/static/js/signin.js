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
    
    // Enhanced logging for debugging
    console.log('=== OAuth Callback Debug Info ===');
    console.log('Full URL:', window.location.href);
    console.log('Search params:', window.location.search);
    console.log('URL Params object:', Object.fromEntries(urlParams));
    console.log('Checking for OAuth callback params:', { 
        hasCode: !!code, 
        hasError: !!error,
        code: code ? `${code.substring(0, 30)}...` : null,
        codeLength: code ? code.length : 0,
        error,
        errorDescription 
    });
    
    if (error) {
        console.error('OAuth error in URL:', { error, description: errorDescription });
        showError(errorDescription || error);
        // Clean up URL
        window.history.replaceState({}, document.title, '/signin');
        return;
    }
    
    if (code) {
        console.log('Found authorization code, attempting to decode and exchange for session...');
        try {
            // Decode the URL-encoded code
            const decodedCode = decodeURIComponent(code);
            console.log('Decoded code length:', decodedCode.length);
            console.log('Original vs decoded code match:', code === decodedCode);
            
            if (!supabaseClient) {
                throw new Error('Supabase client not initialized');
            }
            
            // Use the exchangeCodeForSession method with the decoded code
            console.log('Calling exchangeCodeForSession...');
            const { data, error: sessionError } = await supabaseClient.auth.exchangeCodeForSession(decodedCode);
            
            if (sessionError) {
                console.error('Session exchange error:', sessionError);
                console.error('Error details:', {
                    message: sessionError.message,
                    status: sessionError.status,
                    statusText: sessionError.statusText
                });
                throw sessionError;
            }
            
            if (data?.session) {
                console.log('Session created successfully!');
                console.log('Session data:', {
                    user: data.session.user?.email,
                    accessToken: data.session.access_token ? 'present' : 'missing',
                    expiresAt: data.session.expires_at
                });
                // Clean up URL before redirect
                window.history.replaceState({}, document.title, '/signin');
                // Redirect to profile page
                console.log('Redirecting to profile page...');
                window.location.href = '/profile';
                return;
            } else {
                throw new Error('No session created from code exchange - data.session is missing');
            }
        } catch (error) {
            console.error('Error exchanging code for session:', error);
            console.error('Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            
            // Handle specific error cases
            if (error.message?.includes('Invalid authorization code')) {
                showError('Authorization code has expired. Please try signing in again.');
            } else if (error.message?.includes('code_verifier')) {
                showError('PKCE verification failed. Please try signing in again.');
            } else if (error.message?.includes('fetch')) {
                showError('Network error during authentication. Please check your connection and try again.');
            } else {
                showError(`Failed to complete sign-in: ${error.message}`);
            }
            
            // Clean up URL
            window.history.replaceState({}, document.title, '/signin');
        }
    } else {
        console.log('No authorization code found in URL parameters');
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
        errorDisplay.style.border = '1px solid rgba(239, 68, 68, 0.3)';
        
        const authButtons = document.querySelector('.oauth-buttons');
        if (authButtons) {
            authButtons.after(errorDisplay);
        } else {
            document.body.appendChild(errorDisplay);
        }
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
                const span = button.querySelector('span');
                if (span) {
                    span.textContent = isLoading ? 'Signing in...' : 'Sign in with Google';
                }
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
                console.error('OAuth initiation error:', error);
                throw error;
            }

            if (data?.url) {
                console.log('Redirecting to Google OAuth:', data.url);
                // Don't use window.location.href as it can be blocked by popup blockers
                window.location.replace(data.url);
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
                showError(`Failed to start sign-in: ${error.message}`);
            }
            
            setLoading(false);
        }
    });
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('DOM loaded, initializing authentication...');
        console.log('Current URL:', window.location.href);
        console.log('Current search params:', window.location.search);
        
        await initializeSupabase();
        console.log('Supabase initialized, setting up Google Sign In...');
        await setupGoogleSignIn();
        
        // Handle OAuth callback if code is present
        console.log('Checking for OAuth callback...');
        await handleAuthCallback();
        
    } catch (error) {
        console.error('Initialization error:', error);
        showError('Failed to initialize authentication. Please refresh the page and try again.');
    }
}); 
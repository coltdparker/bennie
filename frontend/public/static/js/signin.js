document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signinForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const signinButton = document.getElementById('signinButton');
    const emailError = document.getElementById('emailError');
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    const googleSignInButton = document.getElementById('googleSignIn');
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

    // Handle forgot password
    forgotPasswordLink.addEventListener('click', async (e) => {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        if (!email) {
            showError('Please enter your email address first');
            return;
        }

        if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
            showError('Please enter a valid email address');
            return;
        }

        try {
            setLoading(true);
            
            const response = await fetch('/api/auth/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to send reset email');
            }

            // Show success message
            emailError.textContent = 'Password reset email sent. Please check your inbox.';
            emailError.style.color = 'var(--success-green)';
            emailError.style.display = 'block';

        } catch (error) {
            showError(error.message || 'Failed to send reset email');
        } finally {
            setLoading(false);
        }
    });

    // Handle Google Sign In
    googleSignInButton.addEventListener('click', async () => {
        try {
            hideError();
            setLoading(true);

            // Generate and store state parameter
            const state = btoa(crypto.randomUUID());
            sessionStorage.setItem('oauth_state', state);

            // Initialize Supabase client
            const { data, error } = await window.supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: `${window.location.origin}/profile`,
                    queryParams: {
                        state: state,
                        access_type: 'offline',
                        prompt: 'consent'
                    }
                }
            });

            if (error) throw error;

            // The redirect will happen automatically
            console.log('Redirecting to Google sign in...');

        } catch (error) {
            console.error('Google sign-in error:', error);
            
            // Handle specific error cases
            if (error.message?.includes('popup_closed_by_user')) {
                showError('Sign-in was cancelled. Please try again.', true);
            } else if (error.message?.includes('configuration')) {
                showError('Authentication service is not properly configured. Please try again later.');
            } else if (error.message?.includes('network')) {
                showError('Network error. Please check your internet connection and try again.');
            } else {
                showError('Failed to initialize sign-in. Please try again.');
            }
            
            setLoading(false);
        }
    });

    // Handle OAuth redirect result
    window.addEventListener('load', async () => {
        try {
            const hash = window.location.hash;
            if (!hash) return;

            // Check for error in redirect
            const errorParam = new URLSearchParams(hash.substring(1)).get('error');
            if (errorParam) {
                showError(`Authentication failed: ${errorParam}`);
                return;
            }

            // Verify state parameter
            const state = new URLSearchParams(hash.substring(1)).get('state');
            const storedState = sessionStorage.getItem('oauth_state');
            
            if (state !== storedState) {
                showError('Invalid authentication state. Please try again.');
                return;
            }

            // Clear stored state
            sessionStorage.removeItem('oauth_state');

            // Handle the redirect result
            const { data: { session }, error } = await window.supabase.auth.getSession();
            
            if (error) throw error;
            if (!session) throw new Error('Failed to establish session');

            // Redirect to profile
            window.location.href = '/profile';

        } catch (error) {
            console.error('OAuth redirect error:', error);
            showError('Failed to complete sign-in. Please try again.');
        }
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('Form submission started');
        hideError();

        const email = emailInput.value.trim();
        const password = passwordInput.value;
        
        // Basic validation
        if (!email || !password) {
            console.warn('Empty email or password submitted');
            showError('Please enter both email and password');
            return;
        }

        if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
            console.warn('Invalid email format:', email);
            showError('Please enter a valid email address');
            return;
        }

        try {
            console.log('Setting loading state before API call');
            setLoading(true);

            // Send sign-in request to backend
            console.log('Making API request to /api/auth/signin');
            const response = await fetch('/api/auth/signin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            console.log('API Response status:', response.status);
            const data = await response.json();
            console.log('API Response data:', data);

            if (!response.ok) {
                console.error('API error response:', data);
                throw new Error(data.detail || 'Authentication failed');
            }

            // Store session data
            if (data.session) {
                localStorage.setItem('supabase.auth.token', data.session.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
            }

            // Redirect to profile page
            window.location.href = '/profile';

        } catch (error) {
            console.error('Sign-in error:', error);
            showError(error.message || 'Failed to sign in. Please try again.');
        } finally {
            setLoading(false);
        }
    });
}); 
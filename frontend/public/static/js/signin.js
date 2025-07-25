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
    const showError = (message) => {
        console.error('Error displaying:', message);
        emailError.textContent = message;
        emailError.style.display = 'block';
    };

    // Helper function to hide error message
    const hideError = () => {
        console.log('Clearing error display');
        emailError.style.display = 'none';
    };

    // Helper function to set loading state
    const setLoading = (isLoading) => {
        console.log('Setting loading state:', isLoading);
        signinButton.disabled = isLoading;
        signinButton.querySelector('span').textContent = isLoading ? 'Signing in...' : 'Sign In';
        
        // Toggle loading spinner
        const spinner = signinButton.querySelector('.spinner');
        if (spinner) {
            spinner.style.display = isLoading ? 'inline-block' : 'none';
        }
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

            // Initialize Supabase client (make sure supabase-js is included in your HTML)
            const { data, error } = await window.supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: `${window.location.origin}/profile`
                }
            });

            if (error) throw error;

            // The redirect will happen automatically
            console.log('Redirecting to Google sign in...');

        } catch (error) {
            console.error('Google sign-in error:', error);
            showError('Failed to initialize Google sign-in. Please try again.');
            setLoading(false);
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
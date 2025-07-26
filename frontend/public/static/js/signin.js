document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signinForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const signinButton = document.getElementById('signinButton');
    const emailError = document.getElementById('emailError');

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
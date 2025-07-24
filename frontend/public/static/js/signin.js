document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signinForm');
    const emailInput = document.getElementById('email');
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
        if (isLoading) {
            form.classList.add('loading');
            signinButton.disabled = true;
            signinButton.innerHTML = `
                <span>Sending...</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" stroke-linecap="round">
                        <animateTransform
                            attributeName="transform"
                            attributeType="XML"
                            type="rotate"
                            from="0 12 12"
                            to="360 12 12"
                            dur="1s"
                            repeatCount="indefinite"
                        />
                    </path>
                </svg>
            `;
        } else {
            form.classList.remove('loading');
            signinButton.disabled = false;
            signinButton.innerHTML = `
                <span>Send Magic Link</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                </svg>
            `;
        }
    };

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('Form submission started');
        hideError();

        const email = emailInput.value.trim();
        console.log('Attempting sign in for email:', email);
        
        // Basic email validation
        if (!email) {
            console.warn('Empty email submitted');
            showError('Please enter your email address');
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
                body: JSON.stringify({ email }),
            });

            console.log('API Response status:', response.status);
            const data = await response.json();
            console.log('API Response data:', data);

            if (!response.ok) {
                console.error('API error response:', data);
                throw new Error(data.detail || data.message || 'Failed to send magic link');
            }

            // Show success message
            console.log('Showing success message');
            emailInput.value = '';
            form.innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--success-green)" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M22 4L12 14.01l-3-3" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <h3 style="color: var(--success-green); margin: 16px 0;">Check your email!</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 16px;">
                        We've sent a magic link to <strong>${email}</strong>
                    </p>
                    <p style="color: var(--text-light); font-size: 14px;">
                        Click the link in the email to sign in to your account.
                    </p>
                </div>
            `;
        } catch (error) {
            console.error('Error in sign-in process:', error);
            showError(error.message || 'Something went wrong. Please try again.');
        } finally {
            console.log('Resetting loading state');
            setLoading(false);
        }
    });

    // Clear error when user types
    emailInput.addEventListener('input', () => {
        console.log('Input changed, clearing error');
        hideError();
    });
}); 
// DOM Elements
const emailInput = document.getElementById('emailInput');
const emailButton = document.getElementById('emailButton');
const emailContainer = document.getElementById('emailContainer');
const formSection = document.getElementById('formSection');
const successSection = document.getElementById('successSection');
const userForm = document.getElementById('userForm');
const nameInput = document.getElementById('nameInput');
const submitButton = document.getElementById('submitButton');

// State
let selectedLanguage = null;
let userEmail = '';

// Function to get fresh language button references
function getLanguageButtons() {
    return document.querySelectorAll('.language-btn');
}

// Email validation
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Handle email input and button click
function handleEmailSubmit() {
    const email = emailInput.value.trim();
    
    if (!email) {
        showError('Please enter your email address');
        return;
    }
    
    if (!isValidEmail(email)) {
        showError('Please enter a valid email address');
        return;
    }
    
    userEmail = email;
    showForm();
}

// Show error message
function showError(message) {
    // Remove existing error
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and show new error
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        color: #dc2626;
        background: #fef2f2;
        border: 1px solid #fecaca;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        font-size: 0.9rem;
        text-align: center;
        font-weight: 500;
    `;
    errorDiv.textContent = message;
    
    emailContainer.parentNode.insertBefore(errorDiv, emailContainer.nextSibling);
    
    // Remove error after 3 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 3000);
}

// Show the form section
function showForm() {
    formSection.style.display = 'block';
    formSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Set up language button event listeners after form is visible
    setTimeout(() => {
        setupLanguageButtonListeners();
        // Focus on name input
        nameInput.focus();
    }, 100);
}

// Set up language button event listeners
function setupLanguageButtonListeners() {
    const languageButtons = getLanguageButtons();
    console.log('Setting up language button listeners. Found buttons:', languageButtons.length);
    
    languageButtons.forEach(btn => {
        // Remove any existing listeners to prevent duplicates
        btn.removeEventListener('click', handleLanguageButtonClick);
        btn.removeEventListener('keydown', handleLanguageButtonKeydown);
        
        // Add click listener
        btn.addEventListener('click', () => {
            handleLanguageButtonClick(btn.dataset.language);
        });
        
        // Add keyboard event listeners for Enter and Space
        btn.addEventListener('keydown', (e) => {
            handleLanguageButtonKeydown(e, btn.dataset.language);
        });
        
        // Make buttons focusable for keyboard navigation
        btn.setAttribute('tabindex', '0');
    });
}

// Handle language button click
function handleLanguageButtonClick(language) {
    console.log('Language button clicked:', language);
    handleLanguageSelection(language);
}

// Handle language button keydown
function handleLanguageButtonKeydown(e, language) {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        console.log('Language button keydown:', e.key, 'for language:', language);
        
        // First, select the language
        handleLanguageSelection(language);
        
        // Add a small delay to ensure state is updated
        setTimeout(() => {
            // If name is already filled, submit the form
            const name = nameInput.value.trim();
            console.log('Name value:', name, 'Selected language:', selectedLanguage);
            
            if (name && selectedLanguage) {
                console.log('Attempting to submit form...');
                
                // Try multiple approaches to submit the form
                try {
                    // Method 1: Direct form submission
                    if (userForm.requestSubmit) {
                        console.log('Using requestSubmit method');
                        userForm.requestSubmit();
                    } else {
                        // Method 2: Create and dispatch submit event
                        console.log('Using dispatchEvent method');
                        const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
                        userForm.dispatchEvent(submitEvent);
                    }
                } catch (error) {
                    console.error('Error submitting form:', error);
                    
                    // Method 3: Fallback - call handleFormSubmit directly
                    console.log('Using direct handleFormSubmit call');
                    const mockEvent = { preventDefault: () => {} };
                    handleFormSubmit(mockEvent);
                }
            } else {
                console.log('Name not filled or language not selected, focusing on name input');
                // Focus on name input if not filled
                nameInput.focus();
            }
        }, 10); // Small delay to ensure state updates
    }
}

// Handle language selection
function handleLanguageSelection(language) {
    console.log('handleLanguageSelection called with:', language);
    console.log('Previous selectedLanguage:', selectedLanguage);
    
    selectedLanguage = language;
    
    console.log('New selectedLanguage:', selectedLanguage);
    
    // Update button states
    const languageButtons = getLanguageButtons(); // Get fresh references
    languageButtons.forEach(btn => {
        btn.classList.remove('selected');
        if (btn.dataset.language === language) {
            btn.classList.add('selected');
        }
    });
    
    // Enable submit button if name is filled
    updateSubmitButton();
    
    console.log('Language selection complete. selectedLanguage:', selectedLanguage);
}

// Update submit button state
function updateSubmitButton() {
    const name = nameInput.value.trim();
    const canSubmit = name && selectedLanguage;
    
    console.log('updateSubmitButton - name:', name, 'selectedLanguage:', selectedLanguage, 'canSubmit:', canSubmit);
    
    submitButton.disabled = !canSubmit;
    
    if (canSubmit) {
        submitButton.style.opacity = '1';
        console.log('Submit button enabled');
    } else {
        submitButton.style.opacity = '0.6';
        console.log('Submit button disabled');
    }
}

// Handle form submission
function handleFormSubmit(e) {
    console.log('=== FORM SUBMISSION START ===');
    console.log('Form submission handler called');
    console.log('Event type:', e.type);
    console.log('Event target:', e.target);
    
    e.preventDefault();
    
    const name = nameInput.value.trim();
    console.log('Form submission - Name:', name, 'Language:', selectedLanguage);
    console.log('User email:', userEmail);
    
    if (!name) {
        console.log('ERROR: No name provided');
        showFormError('Please enter your name');
        return;
    }
    
    if (!selectedLanguage) {
        console.log('ERROR: No language selected');
        showFormError('Please select a language');
        return;
    }
    
    console.log('Form validation passed, proceeding with submission...');
    
    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = `
        <span>Setting up your account...</span>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
    `;
    
    // Send data to backend API
    const userData = {
        email: userEmail,
        name: name,
        language: selectedLanguage
    };
    
    console.log('Sending user data to API:', userData);
    
    fetch('/api/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
    })
    .then(response => {
        console.log('API response status:', response.status);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('API response data:', data);
        if (data.success) {
            console.log('SUCCESS: User created successfully');
            showSuccess(name);
        } else {
            throw new Error(data.message || 'Failed to create user');
        }
    })
    .catch(error => {
        console.error('ERROR in form submission:', error);
        showFormError('Failed to create account. Please try again.');
        
        // Reset button
        submitButton.disabled = false;
        submitButton.innerHTML = `
            <span>Start My Language Journey</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
        `;
    });
    
    console.log('=== FORM SUBMISSION END ===');
}

// Show form error
function showFormError(message) {
    // Remove existing error
    const existingError = document.querySelector('.form-error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and show new error
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error-message';
    errorDiv.style.cssText = `
        color: #dc2626;
        background: #fef2f2;
        border: 1px solid #fecaca;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        font-size: 0.9rem;
        text-align: center;
        font-weight: 500;
    `;
    errorDiv.textContent = message;
    
    userForm.insertBefore(errorDiv, submitButton);
    
    // Remove error after 3 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 3000);
}

// Show success section
function showSuccess(name) {
    // Update success message with user's language
    const languageDisplay = document.getElementById('selectedLanguageDisplay');
    const userEmailDisplay = document.getElementById('userEmailDisplay');
    const userNameDisplay = document.getElementById('userNameDisplay');
    
    const languageNames = {
        spanish: 'Spanish',
        french: 'French',
        mandarin: 'Mandarin Chinese',
        japanese: 'Japanese',
        german: 'German',
        italian: 'Italian'
    };
    
    languageDisplay.textContent = languageNames[selectedLanguage];
    userEmailDisplay.textContent = userEmail;
    userNameDisplay.textContent = name;
    
    // Hide form and show success
    formSection.style.display = 'none';
    successSection.style.display = 'block';
    successSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Here you would typically send the data to your backend
    console.log('User data:', {
        email: userEmail,
        name: name,
        language: selectedLanguage
    });
}

// Event Listeners
emailButton.addEventListener('click', handleEmailSubmit);
emailInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleEmailSubmit();
    }
});

// Name input changes and keyboard events
nameInput.addEventListener('input', updateSubmitButton);

// Handle Enter key in name input to focus on language selection
nameInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        console.log('Name input Enter key pressed');
        
        // Get fresh language button references
        const languageButtons = getLanguageButtons();
        console.log('Found language buttons:', languageButtons.length);
        
        // Focus on the first language button
        if (languageButtons.length > 0) {
            console.log('Focusing on first language button');
            languageButtons[0].focus();
        } else {
            console.log('No language buttons found!');
        }
    }
});

// Form submission
userForm.addEventListener('submit', handleFormSubmit);

// Add spinning animation for loading state
const style = document.createElement('style');
style.textContent = `
    .spinning {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }
`;
document.head.appendChild(style);

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== DOM LOADED ===');
    console.log('Email input found:', !!emailInput);
    console.log('Name input found:', !!nameInput);
    console.log('Form section found:', !!formSection);
    console.log('User form found:', !!userForm);
    console.log('Submit button found:', !!submitButton);
    
    // Check if language buttons exist (they shouldn't be visible yet)
    const initialLanguageButtons = getLanguageButtons();
    console.log('Initial language buttons found:', initialLanguageButtons.length);
    
    // Focus on email input when page loads
    emailInput.focus();
    
    // Disable submit button initially
    submitButton.disabled = true;
    
    console.log('=== INITIALIZATION COMPLETE ===');
}); 
// DOM Elements
const emailInput = document.getElementById('emailInput');
const emailButton = document.getElementById('emailButton');
const emailContainer = document.getElementById('emailContainer');
const formSection = document.getElementById('formSection');
const successSection = document.getElementById('successSection');
const userForm = document.getElementById('userForm');
const nameInput = document.getElementById('nameInput');
const languageButtons = document.querySelectorAll('.language-btn');
const submitButton = document.getElementById('submitButton');

// State
let selectedLanguage = null;
let userEmail = '';

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
        color: #e74c3c;
        background: #fdf2f2;
        border: 1px solid #fecaca;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        font-size: 0.9rem;
        text-align: center;
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
    
    // Focus on name input
    setTimeout(() => {
        nameInput.focus();
    }, 500);
}

// Handle language selection
function handleLanguageSelection(language) {
    selectedLanguage = language;
    
    // Update button states
    languageButtons.forEach(btn => {
        btn.classList.remove('selected');
        if (btn.dataset.language === language) {
            btn.classList.add('selected');
        }
    });
    
    // Enable submit button if name is filled
    updateSubmitButton();
}

// Update submit button state
function updateSubmitButton() {
    const name = nameInput.value.trim();
    const canSubmit = name && selectedLanguage;
    
    submitButton.disabled = !canSubmit;
    
    if (canSubmit) {
        submitButton.style.opacity = '1';
    } else {
        submitButton.style.opacity = '0.6';
    }
}

// Handle form submission
function handleFormSubmit(e) {
    e.preventDefault();
    
    const name = nameInput.value.trim();
    
    if (!name) {
        showFormError('Please enter your name');
        return;
    }
    
    if (!selectedLanguage) {
        showFormError('Please select a language');
        return;
    }
    
    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = `
        <span>Setting up your account...</span>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
    `;
    
    // Simulate API call (replace with actual backend integration)
    setTimeout(() => {
        showSuccess(name);
    }, 2000);
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
        color: #e74c3c;
        background: #fdf2f2;
        border: 1px solid #fecaca;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        font-size: 0.9rem;
        text-align: center;
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

// Language button clicks
languageButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        handleLanguageSelection(btn.dataset.language);
    });
});

// Name input changes
nameInput.addEventListener('input', updateSubmitButton);

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
    // Focus on email input when page loads
    emailInput.focus();
    
    // Disable submit button initially
    submitButton.disabled = true;
}); 
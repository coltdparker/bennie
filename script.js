console.log('=== SCRIPT.JS LOADED ===');

// DOM Elements
console.log('About to get DOM elements...');
const emailInput = document.getElementById('emailInput');
console.log('emailInput:', emailInput);
const emailButton = document.getElementById('emailButton');
console.log('emailButton:', emailButton);
const emailContainer = document.getElementById('emailContainer');
console.log('emailContainer:', emailContainer);
const formSection = document.getElementById('formSection');
console.log('formSection:', formSection);
const successSection = document.getElementById('successSection');
console.log('successSection:', successSection);
const userForm = document.getElementById('userForm');
console.log('userForm:', userForm);
const nameInput = document.getElementById('nameInput');
console.log('nameInput:', nameInput);
const submitButton = document.getElementById('submitButton');
console.log('submitButton:', submitButton);

console.log('DOM elements found:', {
    emailInput: !!emailInput,
    emailButton: !!emailButton,
    formSection: !!formSection,
    userForm: !!userForm,
    nameInput: !!nameInput,
    submitButton: !!submitButton
});

// State
console.log('Setting up state variables...');
let selectedLanguage = null;
let userEmail = '';

console.log('=== BASIC SCRIPT LOADED SUCCESSFULLY ===');

// Function to get fresh language button references
function getLanguageButtons() {
    const buttons = document.querySelectorAll('.language-btn');
    console.log('getLanguageButtons() called, found', buttons.length, 'buttons');
    return buttons;
}

// Email validation
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Handle email input and button click
function handleEmailSubmit() {
    console.log('=== EMAIL SUBMISSION START ===');
    const email = emailInput.value.trim();
    console.log('Email value:', email);
    
    if (!email) {
        console.log('ERROR: No email provided');
        return;
    }
    
    if (!isValidEmail(email)) {
        console.log('ERROR: Invalid email format');
        return;
    }
    
    console.log('Email validation passed');
    userEmail = email;
    console.log('User email set to:', userEmail);
    showForm();
    console.log('=== EMAIL SUBMISSION END ===');
}

// Show the form section
function showForm() {
    console.log('=== SHOW FORM START ===');
    formSection.style.display = 'block';
    console.log('Form section displayed');
    
    setTimeout(() => {
        console.log('Setting up language button listeners...');
        setupLanguageButtonListeners();
        nameInput.focus();
        console.log('=== SHOW FORM END ===');
    }, 100);
}

// Set up language button event listeners
function setupLanguageButtonListeners() {
    const languageButtons = getLanguageButtons();
    console.log('Setting up language button listeners. Found buttons:', languageButtons.length);
    
    languageButtons.forEach((btn, index) => {
        console.log(`Setting up button ${index}:`, btn.dataset.language);
        
        btn.addEventListener('click', () => {
            console.log(`Button ${index} (${btn.dataset.language}) clicked`);
            handleLanguageSelection(btn.dataset.language);
        });
        
        btn.addEventListener('keydown', (e) => {
            console.log(`Button ${index} (${btn.dataset.language}) keydown:`, e.key);
            handleLanguageButtonKeydown(e, btn.dataset.language, btn);
        });
        
        btn.setAttribute('tabindex', '0');
    });
    
    console.log('Language button listeners setup complete');
}

// Handle language button keydown
function handleLanguageButtonKeydown(e, language, buttonElement) {
    console.log('=== LANGUAGE BUTTON KEYDOWN ===');
    console.log('Key pressed:', e.key);
    console.log('Language:', language);
    console.log('Button has selected class:', buttonElement.classList.contains('selected'));
    
    if (e.key === 'Enter') {
        e.preventDefault();
        console.log('Enter key pressed on language button');
        
        if (buttonElement.classList.contains('selected')) {
            console.log('Button is already selected, attempting form submission');
            const name = nameInput.value.trim();
            console.log('Name value:', name);
            console.log('Selected language:', selectedLanguage);
            
            if (name && selectedLanguage) {
                console.log('Name and language both present, submitting form');
                submitForm();
            } else {
                console.log('Missing name or language');
                if (!name) {
                    nameInput.focus();
                }
            }
        } else {
            console.log('Button not selected, selecting language');
            handleLanguageSelection(language);
        }
    } else if (e.key === ' ') {
        e.preventDefault();
        console.log('Space key pressed, selecting language');
        handleLanguageSelection(language);
    }
    
    console.log('=== LANGUAGE BUTTON KEYDOWN END ===');
}

// Handle language selection
function handleLanguageSelection(language) {
    console.log('=== LANGUAGE SELECTION START ===');
    console.log('Previous selectedLanguage:', selectedLanguage);
    console.log('New language to select:', language);
    
    selectedLanguage = language;
    
    const languageButtons = getLanguageButtons();
    console.log('Updating button states for', languageButtons.length, 'buttons');
    
    languageButtons.forEach((btn, index) => {
        const wasSelected = btn.classList.contains('selected');
        btn.classList.remove('selected');
        if (btn.dataset.language === language) {
            btn.classList.add('selected');
            console.log(`Button ${index} (${btn.dataset.language}) selected`);
        }
    });
    
    console.log('Language selection complete. selectedLanguage:', selectedLanguage);
    console.log('=== LANGUAGE SELECTION END ===');
}

// Submit form function
function submitForm() {
    console.log('=== SUBMIT FORM START ===');
    
    try {
        if (userForm.requestSubmit) {
            console.log('Using requestSubmit method');
            userForm.requestSubmit();
        } else {
            console.log('Using dispatchEvent method');
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
            userForm.dispatchEvent(submitEvent);
        }
    } catch (error) {
        console.error('Error submitting form:', error);
        const mockEvent = { preventDefault: () => {} };
        handleFormSubmit(mockEvent);
    }
    
    console.log('=== SUBMIT FORM END ===');
}

// Handle form submission
function handleFormSubmit(e) {
    console.log('=== FORM SUBMISSION START ===');
    console.log('Form submission handler called');
    
    e.preventDefault();
    
    const name = nameInput.value.trim();
    console.log('Form submission - Name:', name, 'Language:', selectedLanguage);
    console.log('User email:', userEmail);
    
    if (!name) {
        console.log('ERROR: No name provided');
        return;
    }
    
    if (!selectedLanguage) {
        console.log('ERROR: No language selected');
        return;
    }
    
    console.log('Form validation passed, proceeding with submission...');
    
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
    });
    
    console.log('=== FORM SUBMISSION END ===');
}

// Show success section
function showSuccess(name) {
    console.log('=== SHOW SUCCESS START ===');
    
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
    
    formSection.style.display = 'none';
    successSection.style.display = 'block';
    
    console.log('Success section shown');
    console.log('=== SHOW SUCCESS END ===');
}

// Event Listeners
emailButton.addEventListener('click', handleEmailSubmit);
emailInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        console.log('Email input Enter key pressed');
        handleEmailSubmit();
    }
});

// Form submission
userForm.addEventListener('submit', handleFormSubmit);

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== DOM LOADED ===');
    console.log('Email input found:', !!emailInput);
    console.log('Name input found:', !!nameInput);
    console.log('Form section found:', !!formSection);
    console.log('User form found:', !!userForm);
    console.log('Submit button found:', !!submitButton);
    
    const initialLanguageButtons = getLanguageButtons();
    console.log('Initial language buttons found:', initialLanguageButtons.length);
    
    emailInput.focus();
    submitButton.disabled = true;
    
    console.log('=== INITIALIZATION COMPLETE ===');
});
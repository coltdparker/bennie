// Skill assessment sentences
const skillSentences = [
    { text: "Hello, how are you?", level: 10, category: "Basic Greetings" },
    { text: "My name is [name] and I'm from [country].", level: 20, category: "Self Introduction" },
    { text: "I would like to order a coffee, please.", level: 30, category: "Basic Requests" },
    { text: "What time does the restaurant close?", level: 40, category: "Questions" },
    { text: "I've been studying this language for two years.", level: 50, category: "Past Tense" },
    { text: "If I had more time, I would travel more often.", level: 60, category: "Conditionals" },
    { text: "The weather is beautiful today, isn't it?", level: 65, category: "Conversational" },
    { text: "I'm looking forward to visiting the museum tomorrow.", level: 70, category: "Future Plans" },
    { text: "Despite the rain, we decided to go for a walk.", level: 80, category: "Complex Sentences" },
    { text: "The book that I'm reading is quite fascinating.", level: 85, category: "Advanced Grammar" },
    { text: "I can express my opinions on complex topics fluently.", level: 90, category: "Advanced Communication" },
    { text: "The cultural nuances come naturally to me now.", level: 100, category: "Native-like" }
];

// Language to country mapping for placeholder text
const languageToCountry = {
    spanish: "Spain",
    french: "France",
    mandarin: "China",  // Standardize on mandarin
    japanese: "Japan",
    german: "Germany",
    italian: "Italy"
};

// DOM elements
const onboardForm = document.getElementById('onboardForm');
const skillButtons = document.getElementById('skillButtons');
const learningGoal = document.getElementById('learningGoal');
const targetProficiency = document.getElementById('targetProficiency');
const motivationGoal = document.getElementById('motivationGoal');
const topicsOfInterest = document.getElementById('topicsOfInterest');
const submitButton = document.getElementById('submitButton');
const successOverlay = document.getElementById('successOverlay');
const charCount = document.getElementById('charCount');
const charCount2 = document.getElementById('charCount2');

// Slider elements
const sliderHandle = document.getElementById('sliderHandle');
const speechBubble = document.getElementById('speechBubble');
const levelMarkers = document.querySelectorAll('.level-marker');
const sliderBar = document.querySelector('.slider-bar');

// User data
let userData = {};
let userToken = '';

// Slider level descriptions
const levelDescriptions = {
    1: "Level 1 - Basics\nGreat for travel and simple conversations",
    2: "Level 2 - Getting Comfortable\nI want to have basic conversations and understand more",
    3: "Level 3 - Conversational\nI want to chat naturally with native speakers",
    4: "Level 4 - Advanced\nI want to express complex ideas and understand nuances",
    5: "Level 5 - Fluent\nI'm in it for the long haul and want native level fluency!"
};

// Proficiency mapping (1-5 scale to 20-100)
const proficiencyMapping = {
    1: 20,  // Basics
    2: 40,  // Getting Comfortable
    3: 60,  // Conversational
    4: 80,  // Advanced
    5: 100  // Fluent
};

// Current slider level
let currentLevel = 1;  // Initialize to level 1 (20% proficiency)

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    userToken = urlParams.get('token');
    
    // Initialize slider immediately (regardless of token status)
    console.log('DOM loaded, initializing slider...');
    initializeSlider();
    
    // Fallback: Try to initialize slider again after a short delay
    setTimeout(() => {
        if (!sliderHandle || sliderHandle.style.display === 'none') {
            console.log('Slider not initialized properly, retrying...');
            initializeSlider();
        }
    }, 500);
    
    if (!userToken) {
        showError('Invalid access token. Please check your email link.');
        return;
    }
    
    // Fetch user data from backend
    fetchUserData();
});

async function fetchUserData() {
    try {
        const response = await fetch(`/api/verify-token/${userToken}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                showError('Invalid or expired token. Please check your email link or contact support.');
            } else if (response.status === 400) {
                showError('You have already completed onboarding. Welcome back!');
            } else {
                showError('Failed to load your information. Please try again.');
            }
            return;
        }
        
        const data = await response.json();
        userData = data.user;
        
        updateUserInfo();
        populateSkillButtons();
        setupEventListeners();
        
    } catch (error) {
        console.error('Error fetching user data:', error);
        showError('Failed to load your information. Please try again.');
    }
}

function updateUserInfo() {
    document.querySelectorAll('#userName').forEach(el => el.textContent = userData.name);
    document.querySelectorAll('#userLanguage, #userLanguage2, #userLanguage3, #userLanguage4, #userLanguage5, #userLanguage6').forEach(el => el.textContent = userData.target_language);
    
    // Update the learning goal placeholder with the appropriate country
    const country = languageToCountry[userData.target_language] || 'Spain'; // fallback to Spain
    console.log(`Language: ${userData.target_language}, Country: ${country}`);
    learningGoal.placeholder = `For example: I want to travel to ${country} and have conversations with locals, or I need it for work to communicate with international clients...`;
}

function populateSkillButtons() {
    skillButtons.innerHTML = '';
    
    skillSentences.forEach((sentence, index) => {
        // Debug logging
        console.log(`Creating button for sentence ${index}:`, sentence);
        
        // Validate sentence object
        if (!sentence || typeof sentence !== 'object') {
            console.error(`Invalid sentence object at index ${index}:`, sentence);
            return;
        }
        
        if (!sentence.text || !sentence.level || !sentence.category) {
            console.error(`Missing required properties in sentence at index ${index}:`, sentence);
            return;
        }
        
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'skill-button';
        button.dataset.level = sentence.level;
        
        button.innerHTML = `
            <div style="font-weight: 500; margin-bottom: 5px;">${sentence.text}</div>
            <div style="font-size: 12px; opacity: 0.7;">${sentence.category}</div>
        `;
        
        // Each button toggles only itself
        button.addEventListener('click', () => {
            button.classList.toggle('selected');
        });
        skillButtons.appendChild(button);
    });
}

function setupEventListeners() {
    learningGoal.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = count;
        charCount.style.color = count > 550 ? '#FA7561' : '#6b6b6b';
    });
    
    motivationGoal.addEventListener('input', function() {
        const count = this.value.length;
        charCount2.textContent = count;
        charCount2.style.color = count > 550 ? '#FA7561' : '#6b6b6b';
    });
    
    onboardForm.addEventListener('submit', handleFormSubmit);
}

function initializeSlider() {
    // Debug: Check if elements exist
    console.log('Initializing slider...');
    console.log('sliderHandle:', sliderHandle);
    console.log('speechBubble:', speechBubble);
    console.log('levelMarkers:', levelMarkers);
    console.log('sliderBar:', sliderBar);
    
    // Check if all required elements exist
    if (!sliderHandle || !speechBubble || !levelMarkers.length || !sliderBar) {
        console.error('Slider elements not found!');
        return;
    }
    
    // Set initial state
    updateSlider(1);  // Start at level 1 (20% proficiency)
    
    // Ensure the initial proficiency is set
    const initialProficiency = proficiencyMapping[currentLevel];
    console.log('Initial slider level:', currentLevel);
    console.log('Initial proficiency mapping:', initialProficiency);
    
    // Add click handlers for level markers
    levelMarkers.forEach(marker => {
        marker.addEventListener('click', () => {
            console.log('Level marker clicked:', marker.dataset.level);
            const level = parseInt(marker.dataset.level);
            updateSlider(level);
        });
    });
    
    // Add click handler for slider bar
    sliderBar.addEventListener('click', (e) => {
        console.log('Slider bar clicked');
        const rect = sliderBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        const level = Math.round(percentage * 4) + 1; // Convert to 1-5 range
        updateSlider(Math.max(1, Math.min(5, level)));
    });
    
    // Add drag functionality for slider handle
    let isDragging = false;
    
    sliderHandle.addEventListener('mousedown', () => {
        isDragging = true;
        sliderHandle.style.cursor = 'grabbing';
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const rect = sliderBar.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const percentage = mouseX / rect.width;
        const level = Math.round(percentage * 4) + 1; // Convert to 1-5 range
        updateSlider(Math.max(1, Math.min(5, level)));
    });
    
    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            sliderHandle.style.cursor = 'grab';
        }
    });
    
    // Touch support for mobile
    sliderHandle.addEventListener('touchstart', (e) => {
        e.preventDefault();
        isDragging = true;
    });
    
    document.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        e.preventDefault();
        
        const touch = e.touches[0];
        const rect = sliderBar.getBoundingClientRect();
        const touchX = touch.clientX - rect.left;
        const percentage = touchX / rect.width;
        const level = Math.round(percentage * 4) + 1; // Convert to 1-5 range
        updateSlider(Math.max(1, Math.min(5, level)));
    });
    
    document.addEventListener('touchend', () => {
        isDragging = false;
    });
}

/**
 * Updates the slider UI and form state
 * @param {number} level - The selected level (1-5)
 */
function updateSlider(level) {
    // Input validation
    if (!Number.isInteger(level) || level < 1 || level > 5) {
        console.error('Invalid slider level:', level);
        return;
    }

    // Update UI
    const percentage = ((level - 1) / 4) * 100;
    sliderHandle.style.left = `${percentage}%`;
    sliderHandle.style.display = 'block';

    // Update speech bubble
    const speechBubbleContent = speechBubble.querySelector('.speech-bubble-content');
    const levelText = levelDescriptions[level].split('\n');
    speechBubbleContent.innerHTML = `<strong>${levelText[0]}</strong><br>${levelText[1]}`;

    // Update level markers
    levelMarkers.forEach(marker => {
        const markerLevel = parseInt(marker.dataset.level);
        marker.classList.toggle('active', markerLevel === level);
    });

    // Update form state
    const mappedProficiency = proficiencyMapping[level];
    if (!mappedProficiency) {
        console.error('Failed to map proficiency for level:', level);
        return;
    }

    // Update hidden form fields
    learningGoal.value = levelDescriptions[level];
    targetProficiency.value = mappedProficiency;

    // Debug logging
    console.log('Slider updated:', {
        level,
        percentage,
        mappedProficiency,
        description: levelDescriptions[level]
    });
}

/**
 * Validates the form data before submission
 * @param {Object} formData - The form data to validate
 * @returns {string[]} Array of error messages, empty if valid
 */
function validateFormData(formData) {
    const errors = [];

    // Validate skill level (1-100 scale)
    if (!Number.isInteger(formData.skillLevel) || formData.skillLevel < 1 || formData.skillLevel > 100) {
        errors.push('Please select at least one sentence to assess your current level.');
    }

    // Validate target proficiency (20-100 scale, must be one of the mapped values)
    const validProficiencies = Object.values(proficiencyMapping);
    if (!validProficiencies.includes(formData.targetProficiency)) {
        errors.push('Please select your target proficiency level using the slider.');
    }

    // Validate learning goal text
    if (!formData.learningGoal?.trim()) {
        errors.push('Please select a learning goal using the slider.');
    }

    // Validate motivation goal
    if (!formData.motivationGoal?.trim()) {
        errors.push('Please tell us what motivates you to learn.');
    } else if (formData.motivationGoal.length > 600) {
        errors.push('Motivation text is too long. Please keep it under 600 characters.');
    }

    // Validate topics of interest
    if (!formData.topicsOfInterest?.trim()) {
        errors.push('Please enter at least one topic of interest.');
    }

    return errors;
}

/**
 * Handles form submission
 * @param {Event} e - The submit event
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    // Calculate current skill level
    const selectedButtons = document.querySelectorAll('.skill-button.selected');
    const selectedLevels = Array.from(selectedButtons).map(btn => parseInt(btn.dataset.level));
    const avgLevel = selectedLevels.length > 0 
        ? Math.round(selectedLevels.reduce((a, b) => a + b, 0) / selectedLevels.length)
        : 10; // Default to basic level if nothing selected

    // Prepare form data
    const formData = {
        skillLevel: avgLevel,
        targetProficiency: parseInt(targetProficiency.value),
        learningGoal: learningGoal.value,
        motivationGoal: motivationGoal.value.trim(),
        topicsOfInterest: topicsOfInterest.value.trim()
    };

    // Validate form data
    const errors = validateFormData(formData);
    if (errors.length > 0) {
        showError(errors.join('\n'));
        return;
    }

    // Prepare request data
    const requestData = {
        token: userToken,
        skill_level: formData.skillLevel,
        target_proficiency: formData.targetProficiency,
        learning_goal: formData.learningGoal,
        motivation_goal: formData.motivationGoal,
        topics_of_interest: formData.topicsOfInterest
    };

    // Debug logging
    console.log('Submitting form data:', {
        formData,
        requestData,
        selectedLevels,
        avgLevel
    });

    try {
        // Update button state
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <span>Updating your profile...</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning">
                <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
        `;

        // Submit to backend
        const response = await fetch('/api/complete-onboarding', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(formatErrorMessage(errorData));
        }

        const result = await response.json();
        console.log('Onboarding completed:', result);
        showSuccess();

    } catch (error) {
        console.error('Error completing onboarding:', error);
        showError(error.message || 'Failed to complete onboarding. Please try again.');
        submitButton.disabled = false;
        submitButton.innerHTML = 'Complete My Profile';
    }
}

/**
 * Formats error messages from the API response
 * @param {Object} errorData - The error response from the API
 * @returns {string} Formatted error message
 */
function formatErrorMessage(errorData) {
    if (!errorData) return 'An unknown error occurred';

    if (errorData.detail) {
        if (Array.isArray(errorData.detail)) {
            return errorData.detail
                .map(err => {
                    if (typeof err === 'object' && err.loc && err.msg) {
                        const field = err.loc[err.loc.length - 1];
                        return `${field}: ${err.msg}`;
                    }
                    return err.msg || err.message || JSON.stringify(err);
                })
                .join('\n');
        }
        return errorData.detail;
    }

    return JSON.stringify(errorData);
}

function showError(message) {
    const existingError = document.querySelector('.error-message');
    if (existingError) existingError.remove();
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        color: #dc2626; 
        background: #fef2f2; 
        border: 1px solid #fecaca;
        padding: 0.75rem 1rem; 
        border-radius: 8px; 
        margin-bottom: 20px;
        font-size: 0.9rem; 
        text-align: left;
        font-weight: 500;
        white-space: pre-line;
    `;
    errorDiv.textContent = message;
    onboardForm.insertBefore(errorDiv, onboardForm.firstChild);
    
    // Scroll error into view
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    setTimeout(() => errorDiv.remove(), 8000); // Show for 8 seconds
}

function showSuccess() {
    successOverlay.style.display = 'flex';
    onboardForm.style.pointerEvents = 'none';
    onboardForm.style.opacity = '0.5';

    // Compose Bennie email content
    const name = userData.name || 'friend';
    // Use currentLevel instead of trying to parse the descriptive text
    const goalLevel = currentLevel || 1;
    let exampleLine = "I'll do my best to get you ready for casual conversation!";
    
    // Use the slider level to determine the message
    switch(goalLevel) {
        case 1:
            exampleLine = "I'll help you get comfortable with the basics for travel and simple conversations!";
            break;
        case 2:
            exampleLine = "Let's build your confidence with basic conversations and understanding!";
            break;
        case 3:
            exampleLine = "I'll help you chat naturally with native speakers and feel comfortable in conversations!";
            break;
        case 4:
            exampleLine = "Let's work on expressing complex ideas and understanding the nuances of the language!";
            break;
        case 5:
            exampleLine = "Let's buckle down and start getting you all the way to fluency. If you put in the work, I promise to help you along the way!";
            break;
        default:
            exampleLine = "I'll do my best to get you ready for casual conversation!";
    }
    const emailText = `Hello ${name},<br><br>It's great getting to know your motivation. Can't wait to chat!<br><br>${exampleLine}<br><br>Your pal,<br>Bennie`;
    const emailContentDiv = document.getElementById('bennieEmailContent');
    const emailPlaceholder = document.getElementById('bennieEmailPlaceholder');
    if (emailContentDiv) {
        if (emailPlaceholder) emailPlaceholder.remove();
        emailContentDiv.innerHTML = emailText;
    } else {
        console.error('Could not find bennieEmailContent div!');
    }
}

// Add spinning animation
const style = document.createElement('style');
style.textContent = `
    .spinning { animation: spin 1s linear infinite; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
`;
document.head.appendChild(style); 
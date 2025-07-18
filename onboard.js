// Skill assessment sentences
const skillSentences = [
    { text: "Hello, how are you?", level: 1, category: "Basic Greetings" },
    { text: "My name is [name] and I'm from [country].", level: 2, category: "Self Introduction" },
    { text: "I would like to order a coffee, please.", level: 3, category: "Basic Requests" },
    { text: "What time does the restaurant close?", level: 4, category: "Questions" },
    { text: "I've been studying this language for two years.", level: 5, category: "Past Tense" },
    { text: "If I had more time, I would travel more often.", level: 6, category: "Conditionals" },
    { text: "The weather is beautiful today, isn't it?", level: 7, category: "Conversational" },
    { text: "I'm looking forward to visiting the museum tomorrow.", level: 8, category: "Future Plans" },
    { text: "Despite the rain, we decided to go for a walk.", level: 9, category: "Complex Sentences" },
    { text: "The book that I'm reading is quite fascinating.", level: 10, category: "Advanced Grammar" },
    { text: "I can express my opinions on complex topics fluently.", level: 11, category: "Advanced Communication" },
    { text: "The cultural nuances come naturally to me now.", level: 12, category: "Native-like" }
];

// Language to country mapping for placeholder text
const languageToCountry = {
    spanish: "Spain",
    french: "France",
    chinese: "China",
    mandarin: "China",
    japanese: "Japan",
    german: "Germany",
    italian: "Italy"
};

// DOM elements
const onboardForm = document.getElementById('onboardForm');
const skillButtons = document.getElementById('skillButtons');
const learningGoal = document.getElementById('learningGoal');
const motivationGoal = document.getElementById('motivationGoal');
const topicsOfInterest = document.getElementById('topicsOfInterest');
const submitButton = document.getElementById('submitButton');
const successOverlay = document.getElementById('successOverlay');
const charCount = document.getElementById('charCount');
const charCount2 = document.getElementById('charCount2');

// User data
let userData = {};
let userToken = '';

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    userToken = urlParams.get('token');
    
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
    
    skillSentences.forEach(sentence => {
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

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const selectedButtons = document.querySelectorAll('.skill-button.selected');
    const selectedLevels = Array.from(selectedButtons).map(btn => parseInt(btn.dataset.level));
    // Calculate average difficulty
    const avgLevel = selectedLevels.length > 0 ? Math.round(selectedLevels.reduce((a, b) => a + b, 0) / selectedLevels.length) : 1;
    
    const formData = {
        skillLevel: avgLevel,
        selectedSentences: selectedLevels,
        learningGoal: learningGoal.value.trim(),
        motivationGoal: motivationGoal.value.trim(),
        topicsOfInterest: topicsOfInterest.value.trim()
    };
    
    if (!formData.learningGoal || !formData.motivationGoal || !formData.topicsOfInterest || selectedLevels.length === 0) {
        showError('Please fill in all fields and select at least one sentence!');
        return;
    }
    
    submitButton.disabled = true;
    submitButton.innerHTML = `
        <span>Updating your profile...</span>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
    `;
    
    try {
        // Submit to backend
        const response = await fetch('/api/complete-onboarding', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: userToken,
                skill_level: formData.skillLevel,
                learning_goal: formData.learningGoal,
                motivation_goal: formData.motivationGoal,
                topics_of_interest: formData.topicsOfInterest
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to complete onboarding');
        }
        
        const result = await response.json();
        console.log('Onboarding completed:', result);
        showSuccess();
        
    } catch (error) {
        console.error('Error completing onboarding:', error);
        showError(error.message || 'Failed to complete onboarding. Please try again.');
        
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.innerHTML = 'Complete Onboarding';
    }
}

function showError(message) {
    const existingError = document.querySelector('.error-message');
    if (existingError) existingError.remove();
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        color: #dc2626; background: #fef2f2; border: 1px solid #fecaca;
        padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 20px;
        font-size: 0.9rem; text-align: center; font-weight: 500;
    `;
    errorDiv.textContent = message;
    onboardForm.insertBefore(errorDiv, onboardForm.firstChild);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function showSuccess() {
    successOverlay.style.display = 'flex';
    onboardForm.style.pointerEvents = 'none';
    onboardForm.style.opacity = '0.5';

    // Compose Bennie email content
    const name = userData.name || 'friend';
    const goal = learningGoal.value.trim();
    let exampleLine = "I'll do my best to get you ready for casual conversation!";
    if (goal) {
        if (/fluency|fluent|master/i.test(goal)) {
            exampleLine = "Let's buckle down and start getting you all the way to fluency. If you put in the work, I promise to help you along the way!";
        } else if (/travel|trip|visit|abroad/i.test(goal)) {
            exampleLine = "I'll do my best to get you ready for casual conversation on your travels!";
        } else if (/work|job|business|career|office/i.test(goal)) {
            exampleLine = "Let's get you ready to impress your colleagues and clients at work!";
        } else if (/family|friends|relationship|connect/i.test(goal)) {
            exampleLine = "I'll help you connect with your family and friends in their language!";
        }
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
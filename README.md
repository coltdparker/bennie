# Bennie - AI Language Learning Friend

A beautiful, modern web application for Bennie, an AI-powered language learning service that sends personalized emails in the language you're learning. Features enhanced readability, accessibility, and a refined user experience designed to help users learn languages through natural immersion.

## 🎨 Design Features

- **Modern & Accessible**: Clean design with excellent contrast ratios and readability
- **Responsive**: Works perfectly on desktop, tablet, and mobile devices
- **Interactive**: Smooth animations and engaging user experience
- **Enhanced UX**: Improved form validation, focus states, and visual feedback
- **Color Palette**: 
  - Bittersweet (Coral): `#FA7561`
  - Platinum (Cream): `#E9E2DF`
  - Night (Dark): `#141414`
  - Tan: `#DAB785`
  - Text Primary: `#1a1a1a`
  - Text Secondary: `#4a4a4a`

## 🚀 Features

### User Flow
1. **Email Collection**: Users enter their email address to get started
2. **Personalization**: Users provide their name/nickname
3. **Language Selection**: Choose from 6 supported languages:
   - 🇪🇸 Spanish
   - 🇫🇷 French
   - 🇨🇳 Mandarin Chinese
   - 🇯🇵 Japanese
   - 🇩🇪 German
   - 🇮🇹 Italian
4. **Onboarding Process**:
   - Current skill assessment
   - Learning goal selection (5 proficiency levels)
   - Motivation capture
   - Topics of interest selection
5. **Email Interaction**:
   - Regular language learning emails
   - Personalized content based on level
   - Progress tracking
   - Weekly evaluations

### Technical Features
- **Enhanced Form Validation**: Email format validation and required field checking with improved error messaging
- **Smooth Animations**: CSS transitions and JavaScript animations
- **Accessibility**: Proper contrast ratios, focus states, and keyboard navigation
- **Mobile-First**: Responsive design that works on all devices
- **Modern Fonts**: Inter for body text, Playfair Display for headings
- **Visual Hierarchy**: Clear typography and spacing for optimal readability
- **Backend Integration**: FastAPI server with Supabase database
- **Email System**: SendGrid integration for automated emails
- **AI Integration**: OpenAI GPT-4 for personalized content generation

## 📁 File Structure

```
├── Backend/                # Backend Python modules
│   ├── bennie_email_sender.py    # Email generation and sending
│   ├── new_user_email.py         # Welcome email handling
│   ├── send_weekly_evaluation_email.py  # Evaluation emails
│   └── ...
├── database/              # Database configuration
│   ├── schema.sql        # Supabase schema definition
│   └── setup.py          # Database setup utilities
├── index.html            # Main landing page
├── onboard.html          # Onboarding experience
├── styles.css            # Global styles
├── script.js             # Landing page functionality
├── onboard.js            # Onboarding functionality
├── main.py               # FastAPI server
└── README.md             # Project documentation
```

## 🛠️ Setup

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Set up environment variables**:
   - Create `.env` file with required credentials
   - Configure Supabase, SendGrid, and OpenAI keys
4. **Run the server**: `python main.py`

## 🚀 Deployment

The application is deployed on Railway:
1. Changes pushed to the main branch trigger automatic deployment
2. Railway handles environment variables and service configuration
3. Cron jobs are managed through Railway's scheduling system

## 🎯 Data Structure

### User Profile
```javascript
{
  email: "user@example.com",
  name: "John Doe",
  target_language: "spanish",
  proficiency_level: 20,  // Current level (1-100)
  target_proficiency: 60, // Goal level (20,40,60,80,100)
  topics_of_interest: "travel, cooking, movies",
  motivation_goal: "I want to travel to Spain...",
  is_verified: true
}
```

### Email History
```javascript
{
  user_id: "uuid",
  content: "Email content...",
  is_from_bennie: true,
  difficulty_level: 40,
  is_evaluation: false
}
```

## 🔧 Customization

### Adding New Languages
1. Add language to `languageToCountry` mapping in `onboard.js`
2. Update language buttons in `index.html`
3. Add corresponding email templates and translations

### Changing Colors
Modify the CSS custom properties in `styles.css`:
```css
:root {
    --bittersweet: #FA7561;
    --platinum: #E9E2DF;
    --night: #141414;
    --tan: #DAB785;
    --text-primary: #1a1a1a;
    --text-secondary: #4a4a4a;
    --text-light: #6b6b6b;
    --background-light: #f8f8f8;
    --border-light: #d1d1d1;
    --success-green: #10b981;
    --error-red: #ef4444;
}
```

## 📱 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## 🎨 Design System

### Typography
- **Headings**: Playfair Display (serif)
- **Body**: Inter (sans-serif)

### Spacing
- Consistent 8px grid system
- Section spacing through CSS variables
- Responsive padding and margins

### Animations
- Smooth transitions (0.3s ease)
- Hover effects on interactive elements
- Loading states with spinning animations
- Focus states with brand color accents

### Accessibility
- High contrast ratios (WCAG AA compliant)
- Clear focus indicators
- Proper semantic HTML structure
- Keyboard navigation support

## 📄 License

This project is proprietary software owned by Colt Parker. All rights reserved.

---

Built with ❤️ for Bennie - Your AI language learning companion. 
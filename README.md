# Bennie - AI Language Learning Friend

A beautiful, minimalistic landing page for Bennie, an AI friend that sends personalized emails in the language you're learning.

## 🎨 Design Features

- **Modern & Minimalistic**: Clean design with beautiful typography
- **Responsive**: Works perfectly on desktop, tablet, and mobile devices
- **Interactive**: Smooth animations and engaging user experience
- **Color Palette**: 
  - White: `#ffffff`
  - Cream: `#edd382`
  - Orange: `#fc9e4f`
  - Dark: `#070d0d`
  - Brown: `#7e6551`

## 🚀 Features

### User Flow
1. **Email Collection**: Users enter their email address to get started
2. **Personalization**: Users provide their name/nickname
3. **Language Selection**: Choose from 5 supported languages:
   - 🇪🇸 Spanish
   - 🇫🇷 French
   - 🇨🇳 Mandarin Chinese
   - 🇩🇪 German
   - 🇮🇹 Italian
4. **Confirmation**: Success page with user details

### Technical Features
- **Form Validation**: Email format validation and required field checking
- **Smooth Animations**: CSS transitions and JavaScript animations
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Mobile-First**: Responsive design that works on all devices
- **Modern Fonts**: Inter for body text, Playfair Display for headings

## 📁 File Structure

```
├── index.html          # Main HTML structure
├── styles.css          # All styling and animations
├── script.js           # Interactive functionality
└── README.md           # Project documentation
```

## 🛠️ Setup

1. **Clone or download** the project files
2. **Open `index.html`** in your web browser
3. **That's it!** No build process or dependencies required

## 🎯 Usage

The landing page is ready to use as-is. When users complete the form, their data is logged to the console and can be easily integrated with your backend system.

### Data Structure
When a user submits the form, the following data is collected:
```javascript
{
  email: "user@example.com",
  name: "John Doe",
  language: "spanish" // or "french", "mandarin", "german", "italian"
}
```

## 🔧 Customization

### Adding New Languages
1. Add a new button in `index.html` within the `.language-buttons` div
2. Update the `languageNames` object in `script.js`
3. Add the corresponding flag emoji

### Changing Colors
Modify the CSS custom properties in `styles.css`:
```css
:root {
    --white: #ffffff;
    --cream: #edd382;
    --orange: #fc9e4f;
    --dark: #070d0d;
    --brown: #7e6551;
}
```

## 🔗 Backend Integration

The form is currently set up to log user data to the console. To integrate with your backend:

1. Replace the `setTimeout` in `handleFormSubmit()` with your API call
2. Add proper error handling for failed requests
3. Consider adding loading states and success/error messages

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
- Generous whitespace for readability

### Animations
- Smooth transitions (0.3s ease)
- Hover effects on interactive elements
- Loading states with spinning animations

## 📄 License

This project is open source and available under the MIT License.

---

Built with ❤️ for Bennie - Your AI language learning companion. 
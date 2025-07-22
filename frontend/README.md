# Frontend Directory Structure

This directory contains all frontend-related code and assets for the Bennie application.

## Directory Structure

```
frontend/
├── src/                 # Source files
│   ├── components/      # Future React/Vue components
│   ├── styles/          # Source stylesheets (e.g., SASS)
│   ├── scripts/         # Source JavaScript files
│   ├── index.html      # Main landing page
│   └── onboard.html    # Onboarding page
└── public/             # Public assets
    └── static/         # Static files served directly
        ├── images/     # Image assets
        ├── css/        # Compiled CSS
        └── js/         # Compiled JavaScript
```

## Development

- All source files should be placed in appropriate directories under `src/`
- Static assets (images, compiled CSS, compiled JS) go in `public/static/`
- When adding new static files, update the paths in HTML files to use `/static/` prefix

## Future Improvements

- Add build process for CSS and JavaScript
- Implement component-based architecture
- Add asset optimization pipeline
- Set up development server with hot reloading 
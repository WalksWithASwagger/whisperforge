# Static Assets for WhisperForge

This directory contains the static assets used in the WhisperForge application.

## Directory Structure

```
static/
├── css/
│   ├── main.css          # Main application styles and cyberpunk theme
│   └── production.css    # Production-specific styles (tables, badges, admin panels)
├── js/
│   ├── cookie-consent.js # Cookie consent banner functionality
│   └── ui-interactions.js # UI interactions and animations
└── README.md             # This file
```

## Usage

These assets are loaded by the application using the following functions:

- `local_css()` - Loads the main CSS file
- `add_production_css()` - Loads the production CSS file
- `load_js()` - Loads the JavaScript files

## Adding New Assets

When adding new assets:

1. Place CSS files in the `css` directory
2. Place JavaScript files in the `js` directory
3. Update the corresponding loader function in `app.py`
4. Document the purpose of the asset in this README 
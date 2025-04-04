/**
 * Cookie consent banner functionality - updated for Streamlit compatibility
 */
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize once to prevent duplicate handlers
    if (window.cookieConsentInitialized) {
        return;
    }
    
    // Check if cookies were already accepted
    if (localStorage.getItem('cookies_accepted') === 'true') {
        const cookieBanner = document.querySelector('.cookie-banner');
        if (cookieBanner) {
            cookieBanner.style.display = 'none';
        }
    }
    
    // Set up event listener for the accept button using event delegation
    document.addEventListener('click', function(event) {
        // Check if the clicked element is the cookie banner button
        if (event.target.closest('.cookie-banner button')) {
            localStorage.setItem('cookies_accepted', 'true');
            
            const cookieBanner = document.querySelector('.cookie-banner');
            if (cookieBanner) {
                cookieBanner.style.display = 'none';
            }
        }
    });
    
    // Mark as initialized
    window.cookieConsentInitialized = true;
}); 
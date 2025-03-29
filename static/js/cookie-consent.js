/**
 * Cookie consent banner functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if cookies were already accepted
    if (localStorage.getItem('cookies_accepted') === 'true') {
        const cookieBanner = document.querySelector('.cookie-banner');
        if (cookieBanner) {
            cookieBanner.style.display = 'none';
        }
    }
    
    // Set up event listener for the accept button
    const acceptButton = document.querySelector('.cookie-banner button');
    if (acceptButton) {
        acceptButton.addEventListener('click', function() {
            localStorage.setItem('cookies_accepted', 'true');
            document.querySelector('.cookie-banner').style.display = 'none';
        });
    }
}); 
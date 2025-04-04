/**
 * UI interactions and animations for WhisperForge - updated for Streamlit compatibility
 */
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize once to prevent duplicate handlers
    if (window.uiInteractionsInitialized) {
        return;
    }
    
    // Add scanner line animation only if it doesn't already exist
    if (!document.querySelector('.scanner-line')) {
        const scannerLine = document.createElement('div');
        scannerLine.className = 'scanner-line';
        document.body.appendChild(scannerLine);
    }
    
    // Function to add toast notifications
    window.showToast = function(message, type = 'success') {
        // Remove any existing toasts first
        const existingToasts = document.querySelectorAll('.toast-notification');
        existingToasts.forEach(function(toast) {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        });
        
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        
        if (type === 'error') {
            toast.style.borderLeftColor = 'var(--error)';
        } else if (type === 'warning') {
            toast.style.borderLeftColor = 'var(--warning)';
        } else if (type === 'info') {
            toast.style.borderLeftColor = 'var(--info)';
        }
        
        // Add a close button
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'toast-close';
        closeBtn.style.marginLeft = '10px';
        closeBtn.style.cursor = 'pointer';
        toast.appendChild(closeBtn);
        
        document.body.appendChild(toast);
        
        // Remove toast after 3 seconds
        setTimeout(function() {
            if (document.body.contains(toast)) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                
                // Remove from DOM after animation
                setTimeout(function() {
                    if (document.body.contains(toast)) {
                        document.body.removeChild(toast);
                    }
                }, 300);
            }
        }, 3000);
    };
    
    // Event delegation for user interactions
    document.addEventListener('click', function(event) {
        // Handle toast dismissal
        if (event.target.closest('.toast-close')) {
            const toast = event.target.closest('.toast-notification');
            if (toast) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                
                setTimeout(function() {
                    if (document.body.contains(toast)) {
                        document.body.removeChild(toast);
                    }
                }, 300);
            }
        }
    });
    
    // Mark as initialized
    window.uiInteractionsInitialized = true;
}); 
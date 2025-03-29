/**
 * UI interactions and animations for WhisperForge
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add scanner line animation
    const scannerLine = document.createElement('div');
    scannerLine.className = 'scanner-line';
    document.body.appendChild(scannerLine);
    
    // Function to add toast notifications
    window.showToast = function(message, type = 'success') {
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
        
        document.body.appendChild(toast);
        
        // Remove toast after 3 seconds
        setTimeout(function() {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            
            // Remove from DOM after animation
            setTimeout(function() {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    };
    
    // Add active class to current navigation item
    const currentPage = new URLSearchParams(window.location.search).get('page') || 'home';
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(function(item) {
        const itemPage = new URL(item.href).searchParams.get('page') || 'home';
        if (itemPage === currentPage) {
            item.classList.add('active');
        }
    });
}); 
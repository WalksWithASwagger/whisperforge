/**
 * UI Diagnostics for WhisperForge
 * This script runs diagnostic checks on the UI and reports issues to the console
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 WhisperForge Diagnostics: Starting UI checks...');
    
    // Check if required CSS elements are present
    const diagnosticResults = {
        streamlitApp: !!document.querySelector('.stApp'),
        mainCSS: document.querySelector('.stApp') && 
                 getComputedStyle(document.querySelector('.stApp')).background.includes('linear-gradient'),
        scannerLine: !!document.querySelector('.scanner-line'),
        cookieBanner: !!document.querySelector('.cookie-banner'),
        buttons: document.querySelectorAll('.stButton button').length,
        fileUploader: !!document.querySelector('[data-testid="stFileUploader"]'),
        textInputs: document.querySelectorAll('.stTextArea, .stTextInput').length,
        layoutStructure: !!document.querySelector('.main .block-container')
    };
    
    console.table(diagnosticResults);
    
    // Check z-index hierarchy
    const zIndexCheck = [];
    if (document.querySelector('.stButton button')) {
        zIndexCheck.push({
            element: 'Button',
            zIndex: getComputedStyle(document.querySelector('.stButton button')).zIndex
        });
    }
    
    if (document.querySelector('.scanner-line')) {
        zIndexCheck.push({
            element: 'Scanner Line',
            zIndex: getComputedStyle(document.querySelector('.scanner-line')).zIndex
        });
    }
    
    if (document.querySelector('.cookie-banner')) {
        zIndexCheck.push({
            element: 'Cookie Banner',
            zIndex: getComputedStyle(document.querySelector('.cookie-banner')).zIndex
        });
    }
    
    console.log('Z-Index Hierarchy Check:');
    console.table(zIndexCheck);
    
    // Report any issues found
    const issues = [];
    if (!diagnosticResults.streamlitApp) issues.push('Streamlit app container not found');
    if (!diagnosticResults.mainCSS) issues.push('Main CSS styles not applied properly');
    if (!diagnosticResults.layoutStructure) issues.push('Main layout structure missing');
    if (diagnosticResults.buttons === 0) issues.push('No buttons found - possible rendering issue');
    
    if (issues.length > 0) {
        console.error('⚠️ Issues detected:', issues);
        
        // Create a visible diagnostic panel if there are issues
        const diagnosticPanel = document.createElement('div');
        diagnosticPanel.style.position = 'fixed';
        diagnosticPanel.style.top = '10px';
        diagnosticPanel.style.left = '10px';
        diagnosticPanel.style.zIndex = '9999';
        diagnosticPanel.style.background = 'rgba(0,0,0,0.8)';
        diagnosticPanel.style.color = 'white';
        diagnosticPanel.style.padding = '20px';
        diagnosticPanel.style.borderRadius = '5px';
        diagnosticPanel.style.maxWidth = '80%';
        diagnosticPanel.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
        
        diagnosticPanel.innerHTML = `
            <h3>WhisperForge Diagnostic Results</h3>
            <p>${issues.length} issues detected:</p>
            <ul>${issues.map(issue => `<li>${issue}</li>`).join('')}</ul>
            <p><button id="diagnostic-refresh">Refresh Page</button></p>
        `;
        
        document.body.appendChild(diagnosticPanel);
        
        document.getElementById('diagnostic-refresh').addEventListener('click', function() {
            window.location.reload();
        });
    } else {
        console.log('✅ No UI rendering issues detected');
    }
    
    // Test if JavaScript interactivity is working
    window.diagTestInteractivity = function() {
        if (window.showToast) {
            window.showToast('Diagnostics: JavaScript interactivity is working!', 'info');
            return true;
        }
        return false;
    };
    
    // Run the test after a short delay
    setTimeout(function() {
        const jsInteractive = window.diagTestInteractivity();
        console.log('JavaScript interactivity test:', jsInteractive ? 'PASSED' : 'FAILED');
    }, 2000);
}); 
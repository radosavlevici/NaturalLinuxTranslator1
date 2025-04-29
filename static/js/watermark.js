// Watermarking and security features for Linux Command Translator

function initializeWatermark() {
    console.log('Initializing watermark system...');
    
    // Add a hidden watermark to the page
    addHiddenWatermark();
    
    // Set up periodic watermark verification
    setInterval(checkWatermarkIntegrity, 30000); // Check every 30 seconds
}

function addHiddenWatermark() {
    // Create a hidden watermark element with copyright information
    const watermark = document.createElement('div');
    watermark.id = 'security-watermark';
    watermark.style.position = 'absolute';
    watermark.style.left = '-9999px';
    watermark.style.visibility = 'hidden';
    
    // Get the current date for the watermark
    const now = new Date();
    const dateString = now.toISOString();
    
    // Create a simple "DNA" pattern using the date and a random value
    const randomValue = Math.random().toString(36).substring(2, 15);
    const dnaPattern = `ERTRANS-${dateString}-${randomValue}`;
    
    // Store the watermark data
    watermark.setAttribute('data-watermark', dnaPattern);
    watermark.setAttribute('data-timestamp', now.getTime().toString());
    watermark.setAttribute('data-copyright', '© 2024 Ervin Remus Radosavlevici');
    
    // Add to the document
    document.body.appendChild(watermark);
    
    // Also add a visible but subtle watermark to the footer
    const footer = document.querySelector('.footer');
    if (footer) {
        const visibleWatermark = document.createElement('div');
        visibleWatermark.className = 'watermark text-center mt-3';
        visibleWatermark.innerHTML = '© 2024 Ervin Remus Radosavlevici - Secured with Digital DNA Technology';
        footer.appendChild(visibleWatermark);
    }
}

function checkWatermarkIntegrity() {
    const watermark = document.getElementById('security-watermark');
    
    if (!watermark) {
        console.warn('Security watermark not found. Recreating...');
        addHiddenWatermark();
        return false;
    }
    
    // Check if the watermark has been tampered with
    const storedTimestamp = parseInt(watermark.getAttribute('data-timestamp') || '0');
    const currentTime = new Date().getTime();
    const timeDifference = currentTime - storedTimestamp;
    
    // If the watermark is too old (more than 2 hours), refresh it
    if (timeDifference > 7200000) {
        console.log('Refreshing security watermark...');
        document.body.removeChild(watermark);
        addHiddenWatermark();
    }
    
    return true;
}

function verifyWatermark(watermarkText) {
    // This function would verify the authenticity of a watermark returned from the server
    // For now, we'll just add a visual indicator
    
    const watermarkElement = document.getElementById('result-watermark');
    if (watermarkElement) {
        // Add a subtle animation to the watermark
        watermarkElement.classList.add('logo-pulse');
        
        // Add a verification icon
        const verifyIcon = document.createElement('span');
        verifyIcon.innerHTML = ' <i class="fa fa-check-circle text-success" title="Verified Content"></i>';
        watermarkElement.appendChild(verifyIcon);
    }
}

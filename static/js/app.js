// Main application JavaScript for Linux Command Translator

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeApp();
    
    // Set up the form submission handler
    setupFormHandler();
    
    // Initialize the watermarking system
    initializeWatermark();
});

function initializeApp() {
    console.log('Initializing Linux Command Translator application...');
    
    // Show the about section if requested
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('about')) {
        document.getElementById('about-section').classList.remove('d-none');
        document.getElementById('translation-section').classList.add('d-none');
    }
    
    // Set up the navigation
    const aboutLink = document.getElementById('about-link');
    if (aboutLink) {
        aboutLink.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('about-section').classList.remove('d-none');
            document.getElementById('translation-section').classList.add('d-none');
        });
    }
    
    const homeLink = document.getElementById('home-link');
    if (homeLink) {
        homeLink.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('about-section').classList.add('d-none');
            document.getElementById('translation-section').classList.remove('d-none');
        });
    }
}

function setupFormHandler() {
    const form = document.getElementById('translation-form');
    const resultsContainer = document.getElementById('results-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get the query from the form
            const queryInput = document.getElementById('query-input');
            const query = queryInput.value.trim();
            
            if (!query) {
                showError('Please enter a query to translate.');
                return;
            }
            
            // Show loading indicator
            loadingIndicator.style.display = 'block';
            resultsContainer.innerHTML = '';
            
            // Send the request to the server
            const formData = new FormData();
            formData.append('query', query);
            
            fetch('/translate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading indicator
                loadingIndicator.style.display = 'none';
                
                if (data.success) {
                    // Display the results
                    displayResults(data);
                } else {
                    // Show error message
                    showError(data.error || 'An unknown error occurred.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                loadingIndicator.style.display = 'none';
                showError('An error occurred while communicating with the server. Please try again.');
            });
        });
    }
}

function displayResults(data) {
    const resultsContainer = document.getElementById('results-container');
    
    // Create results HTML
    const resultsHTML = `
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-dark text-light">
                <h5 class="mb-0">Translation Result</h5>
            </div>
            <div class="card-body">
                <h6 class="card-subtitle mb-3 text-muted">Your Request:</h6>
                <p class="card-text">${escapeHtml(data.natural_language)}</p>
                
                <hr class="my-4">
                
                <h6 class="card-subtitle mb-3">Linux Command:</h6>
                <div class="terminal-output command-block">
                    ${escapeHtml(data.command)}
                </div>
                
                <h6 class="card-subtitle mb-3 mt-4">Explanation:</h6>
                <div class="explanation-block">
                    ${formatExplanation(data.explanation)}
                </div>
                
                <div class="watermark" id="result-watermark">
                    ${escapeHtml(data.watermark)}
                </div>
            </div>
        </div>
    `;
    
    // Display the results
    resultsContainer.innerHTML = resultsHTML;
    
    // Apply the watermark verification
    verifyWatermark(data.watermark);
}

function formatExplanation(explanation) {
    // Convert line breaks to <br> tags
    return escapeHtml(explanation).replace(/\n/g, '<br>');
}

function showError(message) {
    const resultsContainer = document.getElementById('results-container');
    
    resultsContainer.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="fa fa-exclamation-triangle me-2"></i>
            ${escapeHtml(message)}
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Function to copy command to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(
        function() {
            // Show a success message
            const toast = document.createElement('div');
            toast.className = 'position-fixed bottom-0 end-0 p-3';
            toast.innerHTML = `
                <div class="toast align-items-center text-white bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="fa fa-check me-2"></i> Command copied to clipboard!
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;
            document.body.appendChild(toast);
            
            // Initialize and show the toast
            const toastEl = new bootstrap.Toast(toast.querySelector('.toast'));
            toastEl.show();
            
            // Remove the toast element after it's hidden
            toast.addEventListener('hidden.bs.toast', function() {
                document.body.removeChild(toast);
            });
        },
        function(err) {
            console.error('Could not copy text: ', err);
        }
    );
}

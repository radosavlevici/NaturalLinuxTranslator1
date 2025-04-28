// Linux Command Translator
// Copyright (c) 2024 Ervin Remus Radosavlevici
// All rights reserved

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const submitButton = document.getElementById('submitButton');
    const resultsCard = document.getElementById('resultsCard');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    
    // Result elements
    const commandResult = document.getElementById('commandResult');
    const explanationResult = document.getElementById('explanationResult');
    const breakdownResult = document.getElementById('breakdownResult');
    const copyButton = document.getElementById('copyCommand');
    const safetyWarningContainer = document.getElementById('safetyWarningContainer');
    const safetyWarningText = document.getElementById('safetyWarningText');
    
    // Watermark elements
    const dnaSignature = document.getElementById('dnaSignature');
    const authenticatedBy = document.getElementById('authenticatedBy');
    
    // Form submission handler
    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        
        if (!query) {
            showError('Please enter a natural language query');
            return;
        }
        
        // Show loading spinner and hide other elements
        loadingSpinner.classList.remove('d-none');
        resultsCard.classList.add('d-none');
        errorMessage.classList.add('d-none');
        submitButton.disabled = true;
        
        // Send request to backend
        fetch('/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to translate command');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading spinner
            loadingSpinner.classList.add('d-none');
            submitButton.disabled = false;
            
            // Display results
            displayResults(data, query);
        })
        .catch(error => {
            // Hide loading spinner
            loadingSpinner.classList.add('d-none');
            submitButton.disabled = false;
            
            // Show error message
            showError(error.message);
        });
    });
    
    // Copy button handler
    copyButton.addEventListener('click', function() {
        const commandText = commandResult.textContent;
        
        navigator.clipboard.writeText(commandText)
            .then(() => {
                // Temporarily change button text to indicate success
                const originalHtml = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="fas fa-check"></i>';
                
                setTimeout(() => {
                    copyButton.innerHTML = originalHtml;
                }, 1500);
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
            });
    });
    
    // Function to display results
    function displayResults(data, originalQuery) {
        // Check if this is an API key required message
        const isApiKeyRequired = data.command === "API_KEY_REQUIRED";
        
        // Set command and explanation
        commandResult.textContent = isApiKeyRequired ? "API Key Required" : data.command;
        explanationResult.textContent = data.explanation;
        
        // Handle command breakdown
        breakdownResult.innerHTML = '';
        if (data.breakdown && typeof data.breakdown === 'object') {
            const dl = document.createElement('dl');
            
            for (const [component, explanation] of Object.entries(data.breakdown)) {
                const dt = document.createElement('dt');
                dt.textContent = component;
                
                const dd = document.createElement('dd');
                dd.textContent = explanation;
                
                dl.appendChild(dt);
                dl.appendChild(dd);
            }
            
            breakdownResult.appendChild(dl);
        } else {
            breakdownResult.textContent = 'No breakdown available';
        }
        
        // Display safety warning if present
        if (data.safety_warning) {
            safetyWarningText.textContent = data.safety_warning;
            safetyWarningContainer.classList.remove('d-none');
            
            // Make it red for API key message
            if (isApiKeyRequired) {
                safetyWarningContainer.classList.remove('alert-warning');
                safetyWarningContainer.classList.add('alert-danger');
            } else {
                safetyWarningContainer.classList.add('alert-warning');
                safetyWarningContainer.classList.remove('alert-danger');
            }
        } else {
            safetyWarningContainer.classList.add('d-none');
        }
        
        // Set watermark information
        if (data.watermark) {
            dnaSignature.textContent = data.watermark.dna_signature;
            authenticatedBy.textContent = data.watermark.authenticated_by;
        }
        
        // Show results card
        resultsCard.classList.remove('d-none');
        
        // Only add to history if it's a real command
        if (!isApiKeyRequired) {
            addToHistory(originalQuery, data.command);
        }
    }
    
    // Function to show error message
    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove('d-none');
        loadingSpinner.classList.add('d-none');
        submitButton.disabled = false;
    }
    
    // Command history functionality for future use
    const commandHistory = [];
    
    function addToHistory(query, command) {
        // Add to in-memory history
        commandHistory.unshift({
            query: query,
            command: command,
            timestamp: new Date().toISOString()
        });
        
        // Limit history size
        if (commandHistory.length > 10) {
            commandHistory.pop();
        }
        
        // Could be used to implement a history feature in the future
    }
    
    // Initialize with focus on the input field
    queryInput.focus();
});

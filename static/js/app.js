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
    const simulationResult = document.getElementById('simulationResult');
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
                copyButton.classList.add('btn-success');
                copyButton.classList.remove('btn-outline-light');
                
                // Show toast notification
                const toast = document.getElementById('copyToast');
                if (toast) {
                    const toastInstance = new bootstrap.Toast(toast);
                    toastInstance.show();
                }
                
                setTimeout(() => {
                    copyButton.innerHTML = originalHtml;
                    copyButton.classList.remove('btn-success');
                    copyButton.classList.add('btn-outline-light');
                }, 1500);
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
                
                // Show error in button
                copyButton.innerHTML = '<i class="fas fa-times"></i>';
                copyButton.classList.add('btn-danger');
                copyButton.classList.remove('btn-outline-light');
                
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                    copyButton.classList.remove('btn-danger');
                    copyButton.classList.add('btn-outline-light');
                }, 1500);
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
            
            // Reset alert classes
            safetyWarningContainer.classList.remove('alert-warning', 'alert-danger', 'alert-info', 'alert-success');
            
            if (isApiKeyRequired) {
                // API key required message
                safetyWarningContainer.classList.add('alert-danger');
            } else if (data.risk_level !== undefined) {
                // Apply appropriate alert style based on risk level
                const riskClasses = {
                    0: 'alert-success',  // Safe
                    1: 'alert-info',     // Low risk
                    2: 'alert-warning',  // Medium risk
                    3: 'alert-danger'    // High risk
                };
                
                safetyWarningContainer.classList.add(riskClasses[data.risk_level] || 'alert-warning');
                
                // Add risk level icon
                const riskIcons = {
                    0: '<i class="fas fa-check-circle me-2"></i>',
                    1: '<i class="fas fa-info-circle me-2"></i>', 
                    2: '<i class="fas fa-exclamation-circle me-2"></i>',
                    3: '<i class="fas fa-exclamation-triangle me-2"></i>'
                };
                
                if (riskIcons[data.risk_level]) {
                    safetyWarningText.innerHTML = riskIcons[data.risk_level] + safetyWarningText.textContent;
                }
            } else {
                // Default warning for other cases
                safetyWarningContainer.classList.add('alert-warning');
            }
        } else {
            safetyWarningContainer.classList.add('d-none');
        }
        
        // Display simulation results if present
        if (simulationResult) {
            if (data.simulation) {
                simulationResult.textContent = data.simulation;
                simulationResult.parentElement.parentElement.classList.remove('d-none');
            } else {
                simulationResult.textContent = 'No simulation available';
                simulationResult.parentElement.parentElement.classList.add('d-none');
            }
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
    
    // Command history functionality
    const commandHistory = [];
    const historyLimit = 10;
    
    // Get history container DOM elements
    const historyContainer = document.getElementById('historyContainer');
    const historyList = document.getElementById('historyList');
    const historyToggleBtn = document.getElementById('historyToggleBtn');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    
    // Initialize history toggle button
    if (historyToggleBtn) {
        historyToggleBtn.addEventListener('click', function() {
            historyContainer.classList.toggle('d-none');
            const isVisible = !historyContainer.classList.contains('d-none');
            historyToggleBtn.innerHTML = isVisible ? 
                '<i class="fas fa-times me-2"></i>Hide History' : 
                '<i class="fas fa-history me-2"></i>Show History';
        });
    }
    
    // Initialize clear history button
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', function() {
            // Clear history array
            commandHistory.length = 0;
            
            // Clear history display
            updateHistoryDisplay();
            
            // Show toast notification
            const toast = document.getElementById('historyToast');
            if (toast) {
                const toastInstance = new bootstrap.Toast(toast);
                toastInstance.show();
            }
        });
    }
    
    function addToHistory(query, command) {
        // Add to in-memory history
        commandHistory.unshift({
            query: query,
            command: command,
            timestamp: new Date().toISOString()
        });
        
        // Limit history size
        if (commandHistory.length > historyLimit) {
            commandHistory.pop();
        }
        
        // Update history display
        updateHistoryDisplay();
    }
    
    function updateHistoryDisplay() {
        if (!historyList) return;
        
        // Clear current history list
        historyList.innerHTML = '';
        
        if (commandHistory.length === 0) {
            // Show empty state
            const emptyItem = document.createElement('li');
            emptyItem.className = 'list-group-item text-center text-muted';
            emptyItem.innerHTML = '<i class="fas fa-info-circle me-2"></i>No command history yet';
            historyList.appendChild(emptyItem);
            return;
        }
        
        // Add history items
        commandHistory.forEach((item, index) => {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item';
            
            // Format timestamp
            const timestamp = new Date(item.timestamp);
            const timeString = timestamp.toLocaleTimeString();
            
            // Create history item content
            listItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">${timeString}</small>
                    <button class="btn btn-sm btn-outline-secondary reuse-btn" data-index="${index}">
                        <i class="fas fa-redo-alt"></i>
                    </button>
                </div>
                <div class="query-text my-1">${item.query}</div>
                <div class="command-text font-monospace text-success small">${item.command}</div>
            `;
            
            historyList.appendChild(listItem);
        });
        
        // Add event listeners to reuse buttons
        document.querySelectorAll('.reuse-btn').forEach(button => {
            button.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                const item = commandHistory[index];
                
                // Fill in the query input
                queryInput.value = item.query;
                
                // Scroll to input
                queryInput.scrollIntoView({ behavior: 'smooth' });
                
                // Focus on input
                queryInput.focus();
            });
        });
    }
    
    // Initialize with focus on the input field
    queryInput.focus();
});

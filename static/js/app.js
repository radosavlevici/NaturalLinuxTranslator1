// Linux Command Translator
// Copyright (c) 2024 Command Translator
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
    const executeButton = document.getElementById('executeCommand');
    const safetyWarningContainer = document.getElementById('safetyWarningContainer');
    const safetyWarningText = document.getElementById('safetyWarningText');
    
    // Execution elements
    const executionSection = document.getElementById('executionSection');
    const executionOutput = document.getElementById('executionOutput');
    const executionStatus = document.getElementById('executionStatus');
    const executionExitCode = document.getElementById('executionExitCode');
    
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
    
    // Execute button handler
    if (executeButton) {
    executeButton.addEventListener('click', function() {
        const commandText = commandResult.textContent.trim();
        
        // If API key is required, show warning
        if (commandText === "API Key Required") {
            showError("Please provide an OpenAI API key to use this feature.");
            return;
        }
        
        // Show loading state
        executeButton.disabled = true;
        const originalHtml = executeButton.innerHTML;
        executeButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
        
        // Clear previous execution results
        executionOutput.textContent = 'Executing command...';
        executionStatus.textContent = 'Running';
        executionStatus.className = 'badge bg-primary';
        executionExitCode.textContent = 'N/A';
        
        // Show execution section
        executionSection.classList.remove('d-none');
        
        // Create working directory input modal if it doesn't exist
        let workingDir = null;
        const workingDirModal = document.getElementById('workingDirModal');
        
        if (!workingDirModal) {
            // Create modal for working directory
            const modal = document.createElement('div');
            modal.classList.add('modal', 'fade');
            modal.id = 'workingDirModal';
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('aria-labelledby', 'workingDirModalLabel');
            modal.setAttribute('aria-hidden', 'true');
            
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content bg-dark">
                        <div class="modal-header">
                            <h5 class="modal-title" id="workingDirModalLabel">Specify Working Directory</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="workingDirInput" class="form-label">Working Directory (optional):</label>
                                <input type="text" class="form-control" id="workingDirInput" placeholder="/path/to/directory">
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirmWorkingDir">Execute Command</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Initialize the modal
            const workingDirModalObj = new bootstrap.Modal(modal);
            
            // Add event listener to the confirm button
            document.getElementById('confirmWorkingDir').addEventListener('click', function() {
                const inputWorkingDir = document.getElementById('workingDirInput').value.trim();
                executeWithWorkingDir(commandText, inputWorkingDir);
                workingDirModalObj.hide();
            });
            
            // Show the modal for directory input
            workingDirModalObj.show();
        } else {
            // If modal already exists, show it
            const workingDirModalObj = new bootstrap.Modal(workingDirModal);
            document.getElementById('confirmWorkingDir').addEventListener('click', function() {
                const inputWorkingDir = document.getElementById('workingDirInput').value.trim();
                executeWithWorkingDir(commandText, inputWorkingDir);
                workingDirModalObj.hide();
            });
            workingDirModalObj.show();
        }
        
        // Function to execute the command with a specific working directory
        function executeWithWorkingDir(commandText, workingDir) {
            // Send request to execute command
            fetch('/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    command: commandText,
                    working_dir: workingDir || null
                }),
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Failed to execute command');
                    });
                }
                return response.json();
            })
            .then(data => {
                // Reset button state
                executeButton.disabled = false;
                executeButton.innerHTML = originalHtml;
                
                // Combine stdout and stderr, prioritizing stderr
                let output = '';
                
                if (data.stderr && data.stderr.trim()) {
                    output = data.stderr;
                    executionStatus.textContent = 'Completed with errors';
                    executionStatus.className = 'badge bg-warning text-dark';
                } else if (data.stdout) {
                    output = data.stdout;
                    executionStatus.textContent = 'Completed successfully';
                    executionStatus.className = 'badge bg-success';
                } else if (data.error) {
                    output = data.error;
                    executionStatus.textContent = 'Error';
                    executionStatus.className = 'badge bg-danger';
                } else {
                    output = 'Command executed with no output';
                    executionStatus.textContent = 'Completed';
                    executionStatus.className = 'badge bg-secondary';
                }
                
                // Create header with system and directory information
                let headerInfo = '';
                if (data.system_info) {
                    headerInfo += `System: ${data.system_info}\n`;
                }
                if (data.current_directory) {
                    headerInfo += `Working Directory: ${data.current_directory}\n`;
                }
                if (headerInfo) {
                    headerInfo += '\n' + '-'.repeat(50) + '\n\n';
                }
                
                // Display execution results with improved formatting
                executionOutput.textContent = headerInfo + output;
                
                // Enhance the display of execution results
                if (output.trim() === '') {
                    executionOutput.textContent = headerInfo + '(No output from command)';
                    executionOutput.classList.add('text-muted');
                } else {
                    executionOutput.classList.remove('text-muted');
                }
                
                // Show exit code and meaning
                if (data.exit_meaning) {
                    executionExitCode.textContent = `${data.exit_code} (${data.exit_meaning})`;
                } else {
                    executionExitCode.textContent = data.exit_code !== undefined ? data.exit_code : 'N/A';
                }
                
                // Color code exit code for better visibility
                if (data.exit_code === 0) {
                    executionExitCode.classList.add('text-success');
                    executionExitCode.classList.remove('text-danger');
                } else if (data.exit_code > 0) {
                    executionExitCode.classList.add('text-danger');
                    executionExitCode.classList.remove('text-success');
                }
                
                // Show toast notification
                const toast = document.getElementById('executeToast');
                if (toast) {
                    // Update toast content based on execution result
                    const toastBody = toast.querySelector('.toast-body');
                    if (data.exit_code === 0) {
                        toastBody.innerHTML = '<i class="fas fa-check-circle me-2"></i>Command executed successfully';
                        toast.classList.remove('text-bg-danger');
                        toast.classList.add('text-bg-dark');
                    } else {
                        toastBody.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Command executed with exit code ' + data.exit_code;
                        toast.classList.remove('text-bg-dark');
                        toast.classList.add('text-bg-danger');
                    }
                    
                    const toastInstance = new bootstrap.Toast(toast);
                    toastInstance.show();
                }
            })
            .catch(error => {
                // Reset button state
                executeButton.disabled = false;
                executeButton.innerHTML = originalHtml;
                
                // Show error in execution result
                executionOutput.textContent = 'Error: ' + error.message;
                executionStatus.textContent = 'Failed';
                executionStatus.className = 'badge bg-danger';
                executionExitCode.textContent = 'N/A';
                
                console.error('Failed to execute command: ', error);
            });
        }
    });
    }
    
    // Function to display results
    function displayResults(data, originalQuery) {
        // Check if this is an API key required message
        const isApiKeyRequired = data.command === "API_KEY_REQUIRED";
        
        // Set command and explanation with proper formatting
        if (isApiKeyRequired) {
            commandResult.textContent = "API Key Required";
            commandResult.classList.add('text-danger');
        } else {
            // Format command with proper spacing and trimming for better display
            const formattedCommand = data.command.trim();
            commandResult.textContent = formattedCommand;
            
            // Apply enhanced styling for better visibility
            commandResult.classList.add('text-success');
            // Let CSS handle the styling
        }
        
        // Format explanation text for better readability
        if (data.explanation) {
            explanationResult.textContent = data.explanation;
            explanationResult.style.fontWeight = 'normal';
        } else {
            explanationResult.textContent = 'No explanation available.';
            explanationResult.style.fontStyle = 'italic';
            explanationResult.style.color = 'var(--bs-secondary)';
        }
        
        // Handle command breakdown with improved styling
        breakdownResult.innerHTML = '';
        if (data.breakdown && typeof data.breakdown === 'object') {
            const dl = document.createElement('dl');
            dl.className = 'mb-0'; // Remove bottom margin
            
            for (const [component, explanation] of Object.entries(data.breakdown)) {
                const dt = document.createElement('dt');
                dt.textContent = component;
                dt.className = 'text-primary fw-bold mb-1'; // Blue color with bold text
                
                const dd = document.createElement('dd');
                dd.textContent = explanation;
                dd.className = 'ms-3 mb-3 pb-2'; // Add left margin and spacing
                if (Object.entries(data.breakdown).length > 1) {
                    dd.className += ' border-bottom border-secondary border-opacity-25'; // Add separator if multiple items
                }
                
                dl.appendChild(dt);
                dl.appendChild(dd);
            }
            
            breakdownResult.appendChild(dl);
        } else {
            breakdownResult.textContent = 'No breakdown available';
            breakdownResult.style.fontStyle = 'italic';
            breakdownResult.style.color = 'var(--bs-secondary)';
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

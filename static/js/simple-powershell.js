/**
 * PowerShell Command Translator (Simple Version)
 * Copyright (c) 2024 Ervin Remus Radosavlevici
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    var queryForm = document.getElementById('queryForm');
    var queryInput = document.getElementById('queryInput');
    var commandResult = document.getElementById('commandResult');
    var executeButton = document.getElementById('executeButton');
    var workingDirInput = document.getElementById('workingDirInput');
    var executionResults = document.getElementById('executionResults');
    
    // Initialize
    if (queryForm) {
        queryForm.addEventListener('submit', handleTranslateQuery);
    }
    
    if (executeButton) {
        executeButton.addEventListener('click', executeCommand);
    }
    
    // Handle translation of natural language query to PowerShell command
    function handleTranslateQuery(event) {
        event.preventDefault();
        
        // Get query text
        var query = queryInput.value.trim();
        if (!query) {
            alert('Please enter a query.');
            return;
        }
        
        // Call API to translate query
        fetch('/translate_powershell', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.error) {
                commandResult.innerHTML = '<div class="alert alert-danger">' + data.error + '</div>';
                return;
            }
            
            // Display command
            commandResult.innerHTML = '<pre><code class="language-powershell">' + data.command + '</code></pre>';
            
            // Enable execute button
            executeButton.disabled = false;
            executeButton.setAttribute('data-command', data.command);
        })
        .catch(function(error) {
            commandResult.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
        });
    }
    
    // Execute PowerShell command
    function executeCommand() {
        var command = executeButton.getAttribute('data-command');
        if (!command) {
            alert('No command to execute. Please translate a query first.');
            return;
        }
        
        var workingDir = workingDirInput.value.trim() || "C:\\Users\\Administrator\\Documents";
        
        // Call API to execute command
        fetch('/execute_powershell', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                command: command,
                working_dir: workingDir
            })
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.error) {
                executionResults.innerHTML = '<div class="alert alert-danger">' + data.error + '</div>';
                return;
            }
            
            var html = '<div class="card mb-3">';
            html += '<div class="card-header">Execution Results</div>';
            html += '<div class="card-body">';
            
            // Status
            if (data.execution_successful) {
                html += '<div class="alert alert-success">Command executed successfully</div>';
            } else {
                html += '<div class="alert alert-danger">Command execution failed</div>';
            }
            
            // Working directory
            html += '<div class="mb-3"><strong>Working Directory:</strong> ' + data.working_dir + '</div>';
            
            // Output
            if (data.stdout) {
                html += '<div class="mb-3"><strong>Output:</strong><pre>' + data.stdout + '</pre></div>';
            }
            
            // Error
            if (data.stderr) {
                html += '<div class="mb-3"><strong>Error:</strong><pre class="text-danger">' + data.stderr + '</pre></div>';
            }
            
            html += '</div></div>';
            
            // Display results
            executionResults.innerHTML = html;
        })
        .catch(function(error) {
            executionResults.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
        });
    }
});
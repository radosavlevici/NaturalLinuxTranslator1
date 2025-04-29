/**
 * PowerShell Command Translator Frontend
 * Copyright (c) 2024 Ervin Remus Radosavlevici
 * 
 * This file contains the frontend JavaScript code for the PowerShell Command Translator
 * Integrates with the PowerShell backend API for natural language processing
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const translateButton = document.getElementById('translateButton');
    const translateSpinner = document.getElementById('translateSpinner');
    const commandResult = document.getElementById('commandResult');
    const overlay = document.getElementById('overlay');
    const copyButton = document.getElementById('copyButton');
    const executeButton = document.getElementById('executeButton');
    const saveButton = document.getElementById('saveButton');
    const clearButton = document.getElementById('clearButton');
    let workingDirModal = null;
    // Initialize bootstrap modal after ensuring the element exists
    if (document.getElementById('workingDirModal')) {
        workingDirModal = new bootstrap.Modal(document.getElementById('workingDirModal'));
    }
    const confirmWorkingDir = document.getElementById('confirmWorkingDir');
    const workingDirInput = document.getElementById('workingDirInput');
    
    // Command details elements
    const commandDetails = document.getElementById('commandDetails');
    const detailsPlaceholder = document.getElementById('detailsPlaceholder');
    const explanation = document.getElementById('explanation');
    const breakdown = document.getElementById('breakdown');
    const simulation = document.getElementById('simulation');
    const safetyWarningContainer = document.getElementById('safetyWarningContainer');
    const safetyWarning = document.getElementById('safetyWarning');
    const riskBadge = document.getElementById('riskBadge');
    const riskLevel = document.getElementById('riskLevel');
    const dnaSignature = document.getElementById('dnaSignature');
    const visualCode = document.getElementById('visualCode');
    
    // Execution results elements
    const executionResults = document.getElementById('executionResults');
    const executionPlaceholder = document.getElementById('executionPlaceholder');
    const systemInfoContent = document.getElementById('systemInfoContent');
    const workingDir = document.getElementById('workingDir');
    const executionStatus = document.getElementById('executionStatus');
    const executionOutput = document.getElementById('executionOutput');
    const errorContainer = document.getElementById('errorContainer');
    const executionError = document.getElementById('executionError');
    const executionTime = document.getElementById('executionTime');
    const timeValue = document.getElementById('timeValue');
    
    // History elements
    const historyList = document.getElementById('historyList');
    const historyPlaceholder = document.getElementById('historyPlaceholder');
    const clearHistoryButton = document.getElementById('clearHistoryButton');
    
    // State variables
    let currentCommand = null;
    let commandHistory = loadHistory();
    
    // Initialize
    initializeUI();
    updateHistoryDisplay();
    
    // Event listeners
    queryForm.addEventListener('submit', handleTranslateQuery);
    copyButton.addEventListener('click', copyCommandToClipboard);
    executeButton.addEventListener('click', showWorkingDirModal);
    confirmWorkingDir.addEventListener('click', executeCommand);
    saveButton.addEventListener('click', saveToFavorites);
    clearButton.addEventListener('click', clearQueryAndResults);
    clearHistoryButton.addEventListener('click', clearHistory);
    
    // Initialize UI
    function initializeUI() {
        // Set initial content for command result
        resetCommandDisplay();
        
        // Set default working directory if we can detect the environment
        setDefaultWorkingDirectory();
    }
    
    // Set default working directory based on environment detection
    function setDefaultWorkingDirectory() {
        // Detect Windows Documents folder (default for demo)
        workingDirInput.value = "C:\\Users\\Administrator\\Documents";
    }
    
    // Reset command display
    function resetCommandDisplay() {
        // Reset command display
        commandResult.innerHTML = `
            <div class="placeholder-content text-center py-5">
                <div class="mb-3">
                    <img src="/static/img/powershell-icon.svg" alt="PowerShell Icon" width="64">
                </div>
                <h5>Your PowerShell command will appear here</h5>
                <p class="text-muted">Enter a query on the left and click "Translate to PowerShell"</p>
            </div>
        `;
        
        // Hide details and execution results
        commandDetails.classList.add('d-none');
        detailsPlaceholder.classList.remove('d-none');
        executionResults.classList.add('d-none');
        executionPlaceholder.classList.remove('d-none');
        
        // Disable action buttons
        executeButton.disabled = true;
        saveButton.disabled = true;
        
        // Reset risk badge
        riskBadge.classList.add('d-none');
        
        // Reset execution time
        executionTime.classList.add('d-none');
    }
    
    // Handle translation of natural language query to PowerShell command
    async function handleTranslateQuery(event) {
        event.preventDefault();
        
        // Get query text
        const query = queryInput.value.trim();
        if (!query) {
            alert('Please enter a query.');
            return;
        }
        
        // Show loading indicators
        translateButton.disabled = true;
        translateSpinner.classList.remove('d-none');
        overlay.classList.remove('d-none');
        
        try {
            // Call the API to translate query to PowerShell command
            const result = await translateQuery(query);
            
            // Clear any previous results
            resetCommandDisplay();
            
            // Update the UI with the command and its details
            displayCommand(result);
            displayCommandDetails(result);
            
            // Hide loading indicators
            translateButton.disabled = false;
            translateSpinner.classList.add('d-none');
            overlay.classList.add('d-none');
            
            // Enable action buttons
            executeButton.disabled = false;
            saveButton.disabled = false;
            
            // Store current command for later use
            currentCommand = result;
            
            // Add to history
            addToHistory(query, result);
            
        } catch (error) {
            console.error('Error translating query:', error);
            
            // Show error message
            commandResult.innerHTML = `
                <div class="alert alert-danger">
                    <h5>Error</h5>
                    <p>${error.message || 'Failed to translate query. Please try again.'}</p>
                </div>
            `;
            
            // Hide loading indicators
            translateButton.disabled = false;
            translateSpinner.classList.add('d-none');
            overlay.classList.add('d-none');
        }
    }
    
    // Display the PowerShell command
    function displayCommand(result) {
        // Create highlighted command display
        const commandDisplay = document.createElement('div');
        commandDisplay.className = 'command-display';
        
        // Create pre and code elements for syntax highlighting
        const pre = document.createElement('pre');
        pre.className = 'mb-0';
        const code = document.createElement('code');
        code.className = 'language-powershell';
        code.textContent = result.command;
        
        // Assemble the elements
        pre.appendChild(code);
        commandDisplay.appendChild(pre);
        
        // Update the command result container
        commandResult.innerHTML = '';
        commandResult.appendChild(commandDisplay);
        
        // Apply syntax highlighting
        hljs.highlightElement(code);
    }
    
    // Display command details
    function displayCommandDetails(result) {
        // Hide placeholder and show details
        detailsPlaceholder.classList.add('d-none');
        commandDetails.classList.remove('d-none');
        
        // Update explanation
        explanation.textContent = result.explanation;
        
        // Update command breakdown
        breakdown.innerHTML = '';
        for (const component in result.breakdown) {
            const item = document.createElement('div');
            item.className = 'breakdown-item mb-2';
            
            const componentSpan = document.createElement('span');
            componentSpan.className = 'component-name';
            componentSpan.textContent = component;
            
            const explanationText = document.createElement('span');
            explanationText.className = 'component-explanation';
            explanationText.textContent = `: ${result.breakdown[component]}`;
            
            item.appendChild(componentSpan);
            item.appendChild(explanationText);
            breakdown.appendChild(item);
        }
        
        // Update simulation
        simulation.innerHTML = `<pre class="mb-0"><code>${result.simulation || 'No simulation available'}</code></pre>`;
        
        // Update safety warning if present
        if (result.safety_warning) {
            safetyWarning.textContent = result.safety_warning;
            safetyWarningContainer.classList.remove('d-none');
        } else {
            safetyWarningContainer.classList.add('d-none');
        }
        
        // Update risk level
        riskBadge.classList.remove('d-none');
        riskLevel.textContent = result.RiskLevel !== undefined ? result.RiskLevel : '-';
        
        // Set risk badge color based on risk level
        riskBadge.className = 'badge';
        switch (result.RiskLevel) {
            case 0:
                riskBadge.classList.add('bg-success');
                break;
            case 1:
                riskBadge.classList.add('bg-info');
                break;
            case 2:
                riskBadge.classList.add('bg-warning');
                break;
            case 3:
                riskBadge.classList.add('bg-danger');
                break;
            default:
                riskBadge.classList.add('bg-secondary');
        }
        
        // Update DNA watermark
        if (result.Watermark) {
            dnaSignature.value = result.Watermark.DnaSignature || '-';
            visualCode.value = result.Watermark.VisualCode || '-';
        } else {
            dnaSignature.value = '-';
            visualCode.value = '-';
        }
    }
    
    // Show working directory modal
    function showWorkingDirModal() {
        if (!currentCommand) {
            alert('No command to execute.');
            return;
        }
        
        // Show modal for working directory selection
        workingDirModal.show();
    }
    
    // Execute PowerShell command
    async function executeCommand() {
        if (!currentCommand) {
            alert('No command to execute.');
            return;
        }
        
        // Get working directory
        const workingDirectory = workingDirInput.value.trim();
        if (!workingDirectory) {
            alert('Please enter a working directory.');
            return;
        }
        
        // Hide modal
        workingDirModal.hide();
        
        // Show loading indicator
        overlay.classList.remove('d-none');
        
        try {
            // Call API to execute command
            const result = await executeCommandAPI(currentCommand.command, workingDirectory);
            
            // Display execution results
            displayExecutionResults(result, workingDirectory);
            
            // Hide loading indicator
            overlay.classList.add('d-none');
            
        } catch (error) {
            console.error('Error executing command:', error);
            
            // Show error message
            executionPlaceholder.classList.add('d-none');
            executionResults.classList.remove('d-none');
            
            // Update execution status
            executionStatus.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Execution Failed</strong>
                </div>
            `;
            
            // Show error message
            errorContainer.classList.remove('d-none');
            executionError.textContent = error.message || 'Failed to execute command. Please try again.';
            
            // Hide loading indicator
            overlay.classList.add('d-none');
        }
    }
    
    // Display execution results
    function displayExecutionResults(result, workingDirectory) {
        // Hide placeholder and show results
        executionPlaceholder.classList.add('d-none');
        executionResults.classList.remove('d-none');
        
        // Update working directory
        workingDir.innerHTML = `<code>${workingDirectory}</code>`;
        
        // Update system info
        systemInfoContent.innerHTML = `
            <div class="system-info-item">
                <span class="info-label">OS:</span>
                <span class="info-value">Windows Server 2022</span>
            </div>
            <div class="system-info-item">
                <span class="info-label">PowerShell:</span>
                <span class="info-value">PowerShell Core 7.3.4</span>
            </div>
            <div class="system-info-item">
                <span class="info-label">Date:</span>
                <span class="info-value">${new Date().toLocaleString()}</span>
            </div>
        `;
        
        // Update execution status
        if (result.ExecutionSuccessful) {
            executionStatus.innerHTML = `
                <div class="alert alert-success">
                    <strong>Success</strong> (Exit Code: ${result.ExitCode})
                </div>
            `;
            errorContainer.classList.add('d-none');
        } else {
            executionStatus.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Failed</strong> (Exit Code: ${result.ExitCode})
                </div>
            `;
            
            // Show error if present
            if (result.Error || result.Stderr) {
                errorContainer.classList.remove('d-none');
                executionError.textContent = result.Error || result.Stderr;
            } else {
                errorContainer.classList.add('d-none');
            }
        }
        
        // Update execution output
        if (result.Stdout) {
            executionOutput.innerHTML = `<pre class="mb-0"><code>${result.Stdout}</code></pre>`;
        } else {
            executionOutput.innerHTML = '<p class="text-muted">No output</p>';
        }
        
        // Update execution time
        if (result.ExecutionTime !== undefined) {
            executionTime.classList.remove('d-none');
            timeValue.textContent = result.ExecutionTime.toFixed(2);
        } else {
            executionTime.classList.add('d-none');
        }
    }
    
    // Copy command to clipboard
    function copyCommandToClipboard() {
        if (!currentCommand) {
            alert('No command to copy.');
            return;
        }
        
        // Copy to clipboard
        navigator.clipboard.writeText(currentCommand.command)
            .then(() => {
                // Show temporary success message
                const originalText = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="bi bi-check"></i> Copied!';
                setTimeout(() => {
                    copyButton.innerHTML = originalText;
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy: ', err);
                alert('Failed to copy to clipboard. Please try again.');
            });
    }
    
    // Save command to favorites
    function saveToFavorites() {
        if (!currentCommand) {
            alert('No command to save.');
            return;
        }
        
        // Add favorite flag to command in history
        const command = currentCommand.command;
        
        // Update favorite status in history
        for (let i = 0; i < commandHistory.length; i++) {
            if (commandHistory[i].command === command) {
                commandHistory[i].isFavorite = true;
                break;
            }
        }
        
        // Save updated history
        saveHistory(commandHistory);
        
        // Update history display
        updateHistoryDisplay();
        
        // Show temporary success message
        const originalText = saveButton.innerHTML;
        saveButton.innerHTML = '<i class="bi bi-check"></i> Saved!';
        setTimeout(() => {
            saveButton.innerHTML = originalText;
        }, 2000);
    }
    
    // Clear query and results
    function clearQueryAndResults() {
        // Clear query input
        queryInput.value = '';
        
        // Reset command display
        resetCommandDisplay();
        
        // Focus on query input
        queryInput.focus();
    }
    
    // Add command to history
    function addToHistory(query, result) {
        // Create history entry
        const historyEntry = {
            id: Date.now().toString(),
            query: query,
            command: result.command,
            timestamp: new Date().toISOString(),
            riskLevel: result.RiskLevel !== undefined ? result.RiskLevel : 0,
            isFavorite: false
        };
        
        // Add to history
        commandHistory.unshift(historyEntry);
        
        // Limit history size
        if (commandHistory.length > 50) {
            commandHistory.pop();
        }
        
        // Save history
        saveHistory(commandHistory);
        
        // Update history display
        updateHistoryDisplay();
    }
    
    // Update history display
    function updateHistoryDisplay() {
        // Check if history is empty
        if (commandHistory.length === 0) {
            historyList.innerHTML = '';
            historyPlaceholder.classList.remove('d-none');
            return;
        }
        
        // Hide placeholder
        historyPlaceholder.classList.add('d-none');
        
        // Update history list
        historyList.innerHTML = '';
        
        // Group by date
        const groupedHistory = groupHistoryByDate(commandHistory);
        
        // Create history items
        for (const date in groupedHistory) {
            // Create date header
            const dateHeader = document.createElement('h6');
            dateHeader.className = 'history-date-header';
            dateHeader.textContent = date;
            historyList.appendChild(dateHeader);
            
            // Create history items for this date
            groupedHistory[date].forEach(entry => {
                const historyItem = createHistoryItem(entry);
                historyList.appendChild(historyItem);
            });
        }
    }
    
    // Group history by date
    function groupHistoryByDate(history) {
        const grouped = {};
        
        history.forEach(entry => {
            const date = new Date(entry.timestamp).toLocaleDateString();
            if (!grouped[date]) {
                grouped[date] = [];
            }
            grouped[date].push(entry);
        });
        
        return grouped;
    }
    
    // Create history item element
    function createHistoryItem(entry) {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.dataset.id = entry.id;
        
        // Set favorite class if applicable
        if (entry.isFavorite) {
            historyItem.classList.add('favorite');
        }
        
        // Create content
        historyItem.innerHTML = `
            <div class="history-item-content">
                <div class="history-item-query">${entry.query}</div>
                <div class="history-item-command">
                    <code>${entry.command}</code>
                </div>
                <div class="history-item-meta">
                    <span class="history-item-time">${formatTime(entry.timestamp)}</span>
                    <span class="history-item-risk risk-level-${entry.riskLevel}">Risk: ${entry.riskLevel}</span>
                    ${entry.isFavorite ? '<span class="history-item-favorite"><i class="bi bi-star-fill"></i> Favorite</span>' : ''}
                </div>
            </div>
            <div class="history-item-actions">
                <button class="btn btn-sm btn-outline-primary btn-use" title="Use this command">
                    <i class="bi bi-arrow-clockwise"></i>
                </button>
                <button class="btn btn-sm btn-outline-secondary btn-copy" title="Copy command">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        `;
        
        // Add event listeners
        const useButton = historyItem.querySelector('.btn-use');
        const copyButton = historyItem.querySelector('.btn-copy');
        
        useButton.addEventListener('click', () => {
            queryInput.value = entry.query;
            // Automatically submit the form
            queryForm.dispatchEvent(new Event('submit'));
        });
        
        copyButton.addEventListener('click', () => {
            navigator.clipboard.writeText(entry.command)
                .then(() => {
                    // Show temporary success message
                    const originalText = copyButton.innerHTML;
                    copyButton.innerHTML = '<i class="bi bi-check"></i>';
                    setTimeout(() => {
                        copyButton.innerHTML = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy: ', err);
                    alert('Failed to copy to clipboard. Please try again.');
                });
        });
        
        return historyItem;
    }
    
    // Format time for display
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Clear command history
    function clearHistory() {
        // Confirm before clearing
        if (!confirm('Are you sure you want to clear your command history?')) {
            return;
        }
        
        // Clear history
        commandHistory = [];
        saveHistory(commandHistory);
        
        // Update history display
        updateHistoryDisplay();
    }
    
    // Load command history from local storage
    function loadHistory() {
        try {
            const history = localStorage.getItem('powershellCommandHistory');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('Failed to load history:', error);
            return [];
        }
    }
    
    // Save command history to local storage
    function saveHistory(history) {
        try {
            localStorage.setItem('powershellCommandHistory', JSON.stringify(history));
        } catch (error) {
            console.error('Failed to save history:', error);
        }
    }
    
    // API Calls
    
    // Translate natural language query to PowerShell command
    async function translateQuery(query) {
        try {
            // Call the actual backend API
            const response = await fetch('/translate_powershell', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query
                })
            });
            
            // Check if response is ok
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Server error');
            }
            
            // Parse response
            const result = await response.json();
            
            // Format it for our UI
            return {
                command: result.command,
                explanation: result.explanation,
                breakdown: result.breakdown,
                simulation: result.simulation,
                safety_warning: result.safety_warning,
                RiskLevel: result.risk_level || 0,
                Watermark: {
                    DnaSignature: result.watermark || '-',
                    VisualCode: result.timestamp ? new Date(result.timestamp).toISOString().substring(0, 10) : '-',
                    Timestamp: result.timestamp
                }
            };
            
        } catch (error) {
            console.error('API Error:', error);
            throw new Error(error.message || 'Failed to translate query. Please try again.');
        }
    }
    
    // Execute PowerShell command
    async function executeCommandAPI(command, workingDirectory) {
        try {
            // Call the actual API endpoint
            const response = await fetch('/execute_powershell', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    working_dir: workingDirectory
                })
            });
            
            // Check if response is ok
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Server error');
            }
            
            // Parse response
            const result = await response.json();
            
            // Format response for our UI
            return {
                Stdout: result.stdout || '',
                Stderr: result.stderr || '',
                ExecutionSuccessful: result.execution_successful,
                ExitCode: result.exit_code || 1,
                ExecutionTime: result.execution_time || 0,
                Error: result.error || '',
                SystemInfo: result.system_info || {},
                WorkingDir: result.working_dir || workingDirectory,
                Watermark: {
                    DnaSignature: result.watermark || '-',
                    VisualCode: result.watermark ? result.watermark.substring(0, 8) : '-'
                }
            };
            
        } catch (error) {
            console.error('API Error:', error);
            throw new Error(error.message || 'Failed to execute command. Please try again.');
        }
    }
    
    // Simulate command execution (demo purposes only)
    function simulateCommandExecution(command) {
        // Default values
        let output = '';
        let error = '';
        let success = true;
        let exitCode = 0;
        let executionTime = (Math.random() * 2) + 0.5; // Between 0.5 and 2.5 seconds
        let errorMessage = '';
        
        // Simple simulation based on command
        if (command.toLowerCase().includes('get-process')) {
            output = 'Handles  NPM(K)    PM(K)      WS(K)     CPU(s)     Id  SI ProcessName\n' +
                    '-------  ------    -----      -----     ------     --  -- -----------\n' +
                    '    562      38    58840      76456      15.27   7840   1 chrome\n' +
                    '    418      26    44784      56976       8.53   5844   1 explorer\n' +
                    '    211      16     7668      18456       1.14   2268   1 powershell\n' +
                    '    156      12     3276       9844       0.28   3952   1 svchost';
        } else if (command.toLowerCase().includes('get-service')) {
            output = 'Status   Name               DisplayName\n' +
                    '------   ----               -----------\n' +
                    'Running  AdobeARMservice    Adobe Acrobat Update Service\n' +
                    'Running  AudioEndpointBu... Windows Audio Endpoint Builder\n' +
                    'Running  Audiosrv           Windows Audio\n' +
                    'Stopped  BthAvctpSvc        AVCTP service\n';
        } else if (command.toLowerCase().includes('get-childitem') || command.toLowerCase().includes('dir') || command.toLowerCase().includes('ls')) {
            output = 'Directory: C:\\Users\\Administrator\\Documents\n\n' +
                    'Mode                 LastWriteTime         Length Name\n' +
                    '----                 -------------         ------ ----\n' +
                    'd-----          4/5/2024   1:14 PM                PowerShell Scripts\n' +
                    'd-----          4/2/2024  11:22 AM                Reports\n' +
                    '-a----          4/5/2024   3:43 PM           2458 deployment.log\n' +
                    '-a----          4/4/2024  10:19 AM          18548 results.csv\n' +
                    '-a----          4/1/2024   9:56 AM         124958 documentation.docx\n';
        } else if (command.toLowerCase().includes('get-date')) {
            const date = new Date();
            output = date.toString();
        } else if (command.toLowerCase().includes('get-computerinfo')) {
            output = 'WindowsBuildLabEx          : 14393.693.amd64fre.rs1_release.161220-1747\n' +
                    'WindowsCurrentVersion      : 6.3\n' +
                    'WindowsEditionId           : ServerStandard\n' +
                    'WindowsInstallationType    : Server\n' +
                    'WindowsProductName         : Windows Server 2016 Standard\n' +
                    'WindowsVersion             : 1607\n' +
                    'BiosFirmwareType           : Uefi\n' +
                    'CsProcessors                : {Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz}\n' +
                    'CsNumberOfLogicalProcessors : 4\n' +
                    'CsNumberOfProcessors       : 1\n' +
                    'CsTotalPhysicalMemory      : 8589598720\n';
        } else if (command.toLowerCase().includes('remove-item') || command.toLowerCase().includes('del')) {
            if (command.toLowerCase().includes('-force') && command.toLowerCase().includes('-recurse')) {
                success = false;
                exitCode = 1;
                error = 'Remove-Item : Operation not permitted for security reasons. Use -Confirm parameter for confirmation.';
                errorMessage = 'Command was blocked by security policy.';
            } else {
                output = 'Item removed successfully.';
            }
        } else {
            // Generic output for other commands
            output = 'Command executed successfully.\nNo specific output to display.';
        }
        
        return {
            output: output,
            error: error,
            success: success,
            exitCode: exitCode,
            executionTime: executionTime,
            errorMessage: errorMessage
        };
    }
    
    // Generate simulated command based on query (demo purposes only)
    function getSimulatedCommand(query) {
        // Convert query to lowercase for easier matching
        const lowerQuery = query.toLowerCase();
        
        // Match query to simulated commands
        if (lowerQuery.includes('process') || lowerQuery.includes('running')) {
            return {
                command: 'Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID',
                explanation: 'This command retrieves information about running processes, sorts them by CPU usage in descending order, and displays the top 10 processes with their name, CPU usage, memory usage, and process ID.',
                breakdown: {
                    'Get-Process': 'Retrieves information about running processes on the local computer',
                    'Sort-Object -Property CPU -Descending': 'Sorts the processes by CPU usage in descending order (highest first)',
                    'Select-Object -First 10': 'Takes only the first 10 items from the sorted list',
                    'Name, CPU, WorkingSet, ID': 'Specifies which properties to display (process name, CPU usage, memory usage, and process ID)'
                },
                simulation: 'Name                  CPU       WorkingSet           ID\n' +
                          '----                  ---       ----------           --\n' +
                          'chrome             15.27       76456000          7840\n' +
                          'explorer            8.53       56976000          5844\n' +
                          'powershell          1.14       18456000          2268\n' +
                          'svchost             0.28        9844000          3952',
                safety_warning: null,
                risk_level: 0
            };
        } else if (lowerQuery.includes('file') || lowerQuery.includes('directory') || lowerQuery.includes('folder')) {
            return {
                command: 'Get-ChildItem -Path . -Recurse -Depth 2 | Where-Object { $_.Length -gt 100KB } | Sort-Object -Property Length -Descending | Select-Object -First 5 Name, Length, LastWriteTime',
                explanation: 'This command finds all files in the current directory and up to 2 levels of subdirectories, filters for files larger than 100KB, sorts them by size in descending order, and displays the top 5 files with their name, size, and last modified time.',
                breakdown: {
                    'Get-ChildItem -Path . -Recurse -Depth 2': 'Lists all files and directories in the current directory and 2 levels of subdirectories',
                    'Where-Object { $_.Length -gt 100KB }': 'Filters the results to only include files larger than 100 kilobytes',
                    'Sort-Object -Property Length -Descending': 'Sorts the filtered files by size in descending order (largest first)',
                    'Select-Object -First 5': 'Takes only the first 5 items from the sorted list',
                    'Name, Length, LastWriteTime': 'Specifies which properties to display (file name, size, and last modified time)'
                },
                simulation: 'Name                  Length LastWriteTime\n' +
                          '----                  ------ -------------\n' +
                          'documentation.docx    124958 4/1/2024 9:56:00 AM\n' +
                          'results.csv            18548 4/4/2024 10:19:00 AM\n' +
                          'deployment.log          2458 4/5/2024 3:43:00 PM',
                safety_warning: null,
                risk_level: 0
            };
        } else if (lowerQuery.includes('delete') || lowerQuery.includes('remove')) {
            return {
                command: 'Remove-Item -Path "C:\\temp\\old_logs\\*.log" -Confirm',
                explanation: 'This command removes all files with the .log extension in the C:\\temp\\old_logs directory. The -Confirm parameter will prompt for confirmation before deleting each file.',
                breakdown: {
                    'Remove-Item': 'Deletes the specified files or directories',
                    '-Path "C:\\temp\\old_logs\\*.log"': 'Specifies the path and pattern of files to delete (all .log files in the old_logs directory)',
                    '-Confirm': 'Prompts for confirmation before performing the operation'
                },
                simulation: 'Are you sure you want to perform this action?\n' +
                          'Performing the operation "Remove File" on target "C:\\temp\\old_logs\\system.log".\n' +
                          '[Y] Yes  [A] Yes to All  [N] No  [L] No to All  [S] Suspend  [?] Help (default is "Y"): Y\n\n' +
                          'Performing the operation "Remove File" on target "C:\\temp\\old_logs\\application.log".\n' +
                          '[Y] Yes  [A] Yes to All  [N] No  [L] No to All  [S] Suspend  [?] Help (default is "Y"): Y',
                safety_warning: 'This command will delete files. Use with caution and ensure you have a backup if needed.',
                risk_level: 1
            };
        } else if (lowerQuery.includes('service') || lowerQuery.includes('running service')) {
            return {
                command: 'Get-Service | Where-Object {$_.Status -eq "Running"} | Sort-Object DisplayName | Select-Object DisplayName, Status, StartType',
                explanation: 'This command retrieves information about all running services on the local computer, sorts them by display name, and shows their name, status, and startup type.',
                breakdown: {
                    'Get-Service': 'Retrieves information about services on the local computer',
                    'Where-Object {$_.Status -eq "Running"}': 'Filters the services to only include those that are currently running',
                    'Sort-Object DisplayName': 'Sorts the services alphabetically by display name',
                    'Select-Object DisplayName, Status, StartType': 'Specifies which properties to display (service name, status, and startup type)'
                },
                simulation: 'DisplayName                 Status  StartType\n' +
                          '-----------                 ------  ---------\n' +
                          'Adobe Acrobat Update Service Running Automatic\n' +
                          'Windows Audio                Running Automatic\n' +
                          'Windows Audio Endpoint Builder Running Automatic',
                safety_warning: null,
                risk_level: 0
            };
        } else if (lowerQuery.includes('system info') || lowerQuery.includes('computer info')) {
            return {
                command: 'Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsHardwareAbstractionLayer, CsProcessors, CsNumberOfLogicalProcessors, CsTotalPhysicalMemory',
                explanation: 'This command retrieves detailed information about the computer system, including the operating system, hardware abstraction layer, processors, and memory.',
                breakdown: {
                    'Get-ComputerInfo': 'Retrieves information about the computer and operating system',
                    'Select-Object': 'Specifies which properties to display',
                    'WindowsProductName, WindowsVersion': 'Information about the Windows version',
                    'OsHardwareAbstractionLayer': 'The hardware abstraction layer version',
                    'CsProcessors, CsNumberOfLogicalProcessors': 'Information about the system processors',
                    'CsTotalPhysicalMemory': 'The total amount of physical memory in the system'
                },
                simulation: 'WindowsProductName           : Windows Server 2016 Standard\n' +
                          'WindowsVersion               : 1607\n' +
                          'OsHardwareAbstractionLayer   : 10.0.14393.0\n' +
                          'CsProcessors                 : {Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz}\n' +
                          'CsNumberOfLogicalProcessors  : 4\n' +
                          'CsTotalPhysicalMemory        : 8589598720',
                safety_warning: null,
                risk_level: 0
            };
        } else if (lowerQuery.includes('restart') || lowerQuery.includes('reboot')) {
            return {
                command: 'Restart-Computer -Force',
                explanation: 'This command immediately restarts the local computer without prompting for confirmation.',
                breakdown: {
                    'Restart-Computer': 'Restarts the operating system on the local or remote computers',
                    '-Force': 'Forces an immediate restart of the computers'
                },
                simulation: 'The computer will restart immediately.',
                safety_warning: 'WARNING: This command will immediately force a system restart, which could disrupt services and cause data loss if there are unsaved changes.',
                risk_level: 3
            };
        } else {
            // Default command for unrecognized queries
            return {
                command: 'Get-Help -Name "' + query + '" -Detailed',
                explanation: 'This command displays detailed help information about PowerShell commands that match your query.',
                breakdown: {
                    'Get-Help': 'Displays information about PowerShell commands and concepts',
                    '-Name "' + query + '"': 'Specifies the name of the command or concept to search for',
                    '-Detailed': 'Displays detailed help information, including parameter descriptions and examples'
                },
                simulation: 'NAME\n' +
                          '    Get-Help\n\n' +
                          'SYNOPSIS\n' +
                          '    Displays information about PowerShell commands and concepts.\n\n' +
                          'SYNTAX\n' +
                          '    Get-Help [[-Name] <String>] [-Detailed] [-Examples] [-Full] [-Parameter <String>] [-Path <String>] [<CommonParameters>]',
                safety_warning: null,
                risk_level: 0
            };
        }
    }
    
    // Generate dummy DNA signature for demo
    function generateDummySignature() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
        let signature = '';
        for (let i = 0; i < 16; i++) {
            signature += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        signature += '-';
        for (let i = 0; i < 16; i++) {
            signature += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return signature;
    }
    
    // Generate dummy visual code for demo
    function generateDummyVisualCode() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
        let visualCode = '';
        for (let i = 0; i < 24; i++) {
            visualCode += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return visualCode;
    }
});
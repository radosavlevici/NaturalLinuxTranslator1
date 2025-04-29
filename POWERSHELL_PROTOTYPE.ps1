# PowerShell Command Translator Prototype
# Copyright (c) 2024 Command Translator
# This script demonstrates the core functionality of the PowerShell Command Translator

# Module imports
using namespace System.Management.Automation
using namespace System.Security.Cryptography
using namespace System.Text

# Configuration
$CONFIG = @{
    ApiEndpoint = "https://api.openai.com/v1/chat/completions"
    Model = "gpt-4o" # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
    MaxTokens = 800
    Temperature = 0.2
    LogPath = "$PSScriptRoot\logs\translator.log"
    HistoryPath = "$PSScriptRoot\data\command_history.json"
    WatermarkKey = "DNA-PS-TRANSLATOR-KEY" # Would be secured in production
    RiskLevels = @{
        0 = "Safe - Read-only operations"
        1 = "Low Risk - Minor modifications"
        2 = "Medium Risk - System configuration changes"
        3 = "High Risk - Potentially destructive operations"
    }
}

# Ensure directories exist
$null = New-Item -Path "$PSScriptRoot\logs" -ItemType Directory -Force
$null = New-Item -Path "$PSScriptRoot\data" -ItemType Directory -Force

# Initialize logging
function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $CONFIG.LogPath -Value $logMessage
    
    # Also output to console for debugging
    if ($Level -eq "ERROR") {
        Write-Host $logMessage -ForegroundColor Red
    } else {
        Write-Host $logMessage -ForegroundColor Gray
    }
}

# Initialize the module
function Initialize-PowerShellTranslator {
    Write-Log "Initializing PowerShell Command Translator"
    
    # Check PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    Write-Log "PowerShell Version: $($psVersion.ToString())"
    
    # Check if OpenAI API key is set
    if (-not $env:OPENAI_API_KEY) {
        Write-Log "OPENAI_API_KEY environment variable not set" -Level "ERROR"
        throw "API key not configured. Please set the OPENAI_API_KEY environment variable."
    }
    
    # Load command history if exists
    if (Test-Path $CONFIG.HistoryPath) {
        try {
            $script:CommandHistory = Get-Content $CONFIG.HistoryPath -Raw | ConvertFrom-Json
            Write-Log "Loaded command history with $($script:CommandHistory.Count) entries"
        } catch {
            Write-Log "Error loading command history: $_" -Level "ERROR"
            $script:CommandHistory = @()
        }
    } else {
        $script:CommandHistory = @()
        Write-Log "Initialized new command history"
    }
    
    Write-Log "PowerShell Command Translator initialized successfully"
}

# Generate DNA-based watermark
function New-CommandWatermark {
    param (
        [string]$Command,
        [datetime]$Timestamp = (Get-Date)
    )
    
    $timestampStr = $Timestamp.ToString("o")
    $contentBytes = [Encoding]::UTF8.GetBytes($Command)
    $timestampBytes = [Encoding]::UTF8.GetBytes($timestampStr)
    $keyBytes = [Encoding]::UTF8.GetBytes($CONFIG.WatermarkKey)
    
    # Generate DNA-like sequence
    $hash1 = [SHA256]::Create().ComputeHash($contentBytes)
    $hash2 = [SHA256]::Create().ComputeHash($timestampBytes)
    
    # Convert to Base64 for compact storage
    $hash1Base64 = [Convert]::ToBase64String($hash1).Substring(0, 16)
    $hash2Base64 = [Convert]::ToBase64String($hash2).Substring(0, 16)
    
    # Combine to create "DNA watermark"
    $dnaWatermark = "$hash1Base64-$hash2Base64"
    
    return @{
        DnaSignature = $dnaWatermark
        Timestamp = $timestampStr
        CommandHash = [Convert]::ToBase64String([SHA256]::Create().ComputeHash($contentBytes))
        Author = "Command Translator"
        VisualCode = [Convert]::ToBase64String([Encoding]::UTF8.GetBytes("$($CONFIG.WatermarkKey):$Command:$timestampStr")).Substring(0, 24)
    }
}

# Validate PowerShell command for safety
function Test-CommandSafety {
    param (
        [string]$Command
    )
    
    # Initialize default return
    $result = @{
        IsSafe = $true
        RiskLevel = 0
        Reason = "Command appears safe"
    }
    
    # Convert to lowercase for pattern matching
    $lowerCommand = $Command.ToLower()
    
    # Check for high-risk patterns
    $highRiskPatterns = @(
        'remove-item.*-recurse.*-force',
        'format-volume',
        'clear-disk',
        'reset-computermachinepassword',
        'stop-computer',
        'restart-computer',
        'remove-partition',
        'remove-windowsfeature',
        'uninstall-windowsfeature',
        'remove-vmhost',
        'set-netlbfoTeam',
        'set-executionpolicy bypass',
        'invoke-expression.*iex',
        'downloadstring',
        'invoke-webrequest.*iwr.*-outfile',
        'new-service'
    )
    
    foreach ($pattern in $highRiskPatterns) {
        if ($lowerCommand -match $pattern) {
            $result.IsSafe = $false
            $result.RiskLevel = 3
            $result.Reason = "Command contains potentially destructive operations: $pattern"
            return $result
        }
    }
    
    # Check for medium-risk patterns
    $mediumRiskPatterns = @(
        'set-item',
        'set-itemproperty',
        'new-item',
        'move-item',
        'set-service',
        'set-location',
        'restart-service',
        'stop-service',
        'set-acl',
        'new-pssession',
        'enter-pssession',
        'invoke-command',
        'enable-psremoting',
        'disable-psremoting',
        'set-aduser',
        'set-adcomputer',
        'set-adgroup'
    )
    
    foreach ($pattern in $mediumRiskPatterns) {
        if ($lowerCommand -match $pattern) {
            $result.RiskLevel = 2
            $result.Reason = "Command contains system configuration changes: $pattern"
        }
    }
    
    # Check for low-risk patterns if not already higher
    if ($result.RiskLevel -lt 2) {
        $lowRiskPatterns = @(
            'out-file',
            'export-csv',
            'add-content',
            'set-content',
            'export-clixml',
            'rename-item',
            'copy-item',
            'new-variable',
            'set-variable',
            'start-process'
        )
        
        foreach ($pattern in $lowRiskPatterns) {
            if ($lowerCommand -match $pattern) {
                $result.RiskLevel = 1
                $result.Reason = "Command contains minor modifications: $pattern"
            }
        }
    }
    
    return $result
}

# Translate natural language to PowerShell command
function ConvertTo-PowerShellCommand {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Query
    )
    
    Write-Log "Translating query: $Query"
    
    # Check if API key is set
    if (-not $env:OPENAI_API_KEY) {
        Write-Log "API key not set" -Level "ERROR"
        return @{
            Command = "API_KEY_REQUIRED"
            Explanation = "An OpenAI API key is required to translate natural language to PowerShell commands."
            Breakdown = @{
                "How to fix" = "Please set the OPENAI_API_KEY environment variable."
            }
            SafetyWarning = "This application requires an OpenAI API key to function properly."
        }
    }
    
    try {
        # Construct prompt for OpenAI
        $systemPrompt = @"
You are a PowerShell command translator. Convert natural language requests into appropriate PowerShell commands.
For each request, provide:
1. The exact PowerShell command to execute
2. A brief explanation of what the command does
3. A breakdown of the command's components
4. A simulation of what would happen if the command is executed

IMPORTANT: Be careful not to generate dangerous commands that could damage systems.
Always favor safety when translating ambiguous requests.
Use PowerShell best practices and modern cmdlets where possible.

Respond with valid JSON in this format:
{
    "command": "the_powershell_command",
    "explanation": "Brief explanation of what the command does",
    "breakdown": {
        "component1": "explanation",
        "component2": "explanation",
        ...
    },
    "simulation": "A text simulation of what the command would output when executed",
    "safety_warning": "Any safety concerns if applicable, otherwise null"
}
"@

        # Prepare API request
        $headers = @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $env:OPENAI_API_KEY"
        }
        
        $body = @{
            model = $CONFIG.Model
            messages = @(
                @{
                    role = "system"
                    content = $systemPrompt
                }
                @{
                    role = "user"
                    content = $Query
                }
            )
            max_tokens = $CONFIG.MaxTokens
            temperature = $CONFIG.Temperature
            response_format = @{ type = "json_object" }
        } | ConvertTo-Json -Depth 10
        
        # Make API request
        Write-Log "Sending request to OpenAI API"
        $response = Invoke-RestMethod -Uri $CONFIG.ApiEndpoint -Method Post -Headers $headers -Body $body
        
        # Parse response
        $result = $response.choices[0].message.content | ConvertFrom-Json
        
        # Validate command for safety
        $command = $result.command
        $safetyCheck = Test-CommandSafety -Command $command
        
        # Add risk level to result
        $result | Add-Member -MemberType NoteProperty -Name "RiskLevel" -Value $safetyCheck.RiskLevel
        
        # Handle dangerous commands
        if (-not $safetyCheck.IsSafe) {
            $result.safety_warning = "⚠️ WARNING: $($safetyCheck.Reason). This command could cause serious system damage and should not be executed."
        } elseif ($safetyCheck.RiskLevel -gt 0) {
            $warningLevels = @{
                1 = "Low risk: "
                2 = "Medium risk: "
            }
            
            if ($result.safety_warning) {
                if (-not $result.safety_warning.StartsWith($warningLevels[$safetyCheck.RiskLevel])) {
                    $result.safety_warning = "$($warningLevels[$safetyCheck.RiskLevel])$($result.safety_warning)"
                }
            } else {
                $result.safety_warning = "$($warningLevels[$safetyCheck.RiskLevel])$($safetyCheck.Reason)"
            }
        }
        
        # Generate watermark
        $watermark = New-CommandWatermark -Command $command
        $result | Add-Member -MemberType NoteProperty -Name "Watermark" -Value $watermark
        
        # Log command request
        $logEntry = @{
            UserQuery = $Query
            GeneratedCommand = $command
            Timestamp = Get-Date
            RiskLevel = $safetyCheck.RiskLevel
            WatermarkId = $watermark.DnaSignature
        }
        
        $script:CommandHistory += $logEntry
        
        # Save updated history
        $script:CommandHistory | ConvertTo-Json -Depth 5 | Set-Content $CONFIG.HistoryPath
        
        Write-Log "Successfully translated query to PowerShell command"
        return $result
        
    } catch {
        Write-Log "Error translating query: $_" -Level "ERROR"
        throw "Failed to process your request: $_"
    }
}

# Execute a PowerShell command safely
function Invoke-SafeCommand {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Command,
        
        [Parameter(Mandatory = $false)]
        [string]$WorkingDirectory = (Get-Location).Path,
        
        [Parameter(Mandatory = $false)]
        [int]$TimeoutSeconds = 15
    )
    
    Write-Log "Executing command: $Command"
    Write-Log "Working directory: $WorkingDirectory"
    
    # Safety check before execution
    $safetyCheck = Test-CommandSafety -Command $Command
    
    if (-not $safetyCheck.IsSafe) {
        Write-Log "Command execution blocked: $($safetyCheck.Reason)" -Level "ERROR"
        return @{
            Error = "Command execution blocked for safety reasons: $($safetyCheck.Reason)"
            Stdout = ""
            Stderr = "ERROR: $($safetyCheck.Reason)"
            Command = $Command
            ExecutionSuccessful = $false
            RiskLevel = $safetyCheck.RiskLevel
            ExitCode = -1
        }
    }
    
    # Generate watermark for audit
    $watermark = New-CommandWatermark -Command $Command
    
    try {
        # Create script block for execution
        $scriptBlock = [ScriptBlock]::Create($Command)
        
        # Prepare for capturing output
        $outputFile = Join-Path $env:TEMP "ps_output_$(Get-Random).txt"
        $errorFile = Join-Path $env:TEMP "ps_error_$(Get-Random).txt"
        
        # Execute in a new PowerShell process with timeout
        $startTime = Get-Date
        
        # Change to working directory if specified
        $originalLocation = Get-Location
        Set-Location -Path $WorkingDirectory
        
        # Execute and capture output
        $job = Start-Job -ScriptBlock {
            param($cmd)
            try {
                # Add execution metadata as comments
                Write-Output "# Executed at: $(Get-Date)"
                Write-Output "# Working directory: $PWD"
                Write-Output "# Command: $cmd"
                Write-Output "# Watermark: $($using:watermark.DnaSignature)"
                Write-Output "# ---------------------------"
                
                # Execute the command
                Invoke-Expression $cmd
            } catch {
                Write-Error "Error executing command: $_"
                throw $_
            }
        } -ArgumentList $Command
        
        # Wait for job with timeout
        $completed = Wait-Job -Job $job -Timeout $TimeoutSeconds
        
        # Reset location
        Set-Location -Path $originalLocation
        
        if ($completed -eq $null) {
            # Job timed out
            Stop-Job -Job $job
            Remove-Job -Job $job -Force
            
            Write-Log "Command execution timed out after $TimeoutSeconds seconds" -Level "ERROR"
            return @{
                Error = "Command execution timed out after $TimeoutSeconds seconds"
                Stdout = ""
                Stderr = "ERROR: Execution exceeded $TimeoutSeconds second timeout"
                Command = $Command
                ExecutionSuccessful = $false
                RiskLevel = $safetyCheck.RiskLevel
                ExitCode = -1
                ExecutionTime = $TimeoutSeconds
                Watermark = $watermark
            }
        }
        
        # Get job output
        $output = Receive-Job -Job $job
        $jobState = $job.State
        $jobError = $job.ChildJobs[0].Error
        
        # Clean up job
        Remove-Job -Job $job -Force
        
        # Calculate execution time
        $executionTime = (Get-Date) - $startTime
        $executionTimeSeconds = $executionTime.TotalSeconds
        
        # Process result
        $result = @{
            Stdout = ($output | Out-String).Trim()
            Stderr = ($jobError | Out-String).Trim()
            ExecutionSuccessful = ($jobState -eq "Completed" -and -not $jobError)
            Command = $Command
            RiskLevel = $safetyCheck.RiskLevel
            ExitCode = if ($jobState -eq "Completed") { 0 } else { 1 }
            ExecutionTime = $executionTimeSeconds
            Watermark = $watermark
        }
        
        # Log execution
        $logEntry = @{
            Command = $Command
            ExecutionTime = Get-Date
            WorkingDirectory = $WorkingDirectory
            ExecutionSuccessful = $result.ExecutionSuccessful
            ExecutionTimeSeconds = $executionTimeSeconds
            WatermarkId = $watermark.DnaSignature
        }
        
        $script:CommandHistory += $logEntry
        
        # Save updated history
        $script:CommandHistory | ConvertTo-Json -Depth 5 | Set-Content $CONFIG.HistoryPath
        
        Write-Log "Command executed successfully in $executionTimeSeconds seconds"
        return $result
        
    } catch {
        Write-Log "Error executing command: $_" -Level "ERROR"
        return @{
            Error = "Failed to execute command: $_"
            Stdout = ""
            Stderr = "Error: $_"
            Command = $Command
            ExecutionSuccessful = $false
            RiskLevel = $safetyCheck.RiskLevel
            ExitCode = -1
            Watermark = $watermark
        }
    }
}

# Main example usage function
function Start-PowerShellTranslatorDemo {
    Initialize-PowerShellTranslator
    
    Write-Host "PowerShell Command Translator Demo" -ForegroundColor Cyan
    Write-Host "Copyright (c) 2024 Command Translator" -ForegroundColor Yellow
    Write-Host "Type 'exit' to quit the demo" -ForegroundColor Gray
    Write-Host ""
    
    while ($true) {
        Write-Host "Enter your query (what you want to do in PowerShell): " -ForegroundColor Green -NoNewline
        $query = Read-Host
        
        if ($query -eq 'exit') {
            break
        }
        
        try {
            # Translate query to PowerShell command
            $result = ConvertTo-PowerShellCommand -Query $query
            
            # Display the result
            Write-Host "`nTranslated Command:" -ForegroundColor Cyan
            Write-Host $result.command -ForegroundColor Yellow
            
            Write-Host "`nExplanation:" -ForegroundColor Cyan
            Write-Host $result.explanation -ForegroundColor White
            
            Write-Host "`nCommand Breakdown:" -ForegroundColor Cyan
            foreach ($key in $result.breakdown.PSObject.Properties.Name) {
                Write-Host "  $key : " -ForegroundColor Gray -NoNewline
                Write-Host $result.breakdown.$key -ForegroundColor White
            }
            
            # Show safety warning if present
            if ($result.safety_warning) {
                Write-Host "`nSafety Warning:" -ForegroundColor Red
                Write-Host $result.safety_warning -ForegroundColor Red
            }
            
            # Show risk level
            $riskColor = switch ($result.RiskLevel) {
                0 { "Green" }
                1 { "Yellow" }
                2 { "DarkYellow" }
                3 { "Red" }
                default { "White" }
            }
            
            Write-Host "`nRisk Level: " -ForegroundColor Cyan -NoNewline
            Write-Host "$($result.RiskLevel) - $($CONFIG.RiskLevels[$result.RiskLevel])" -ForegroundColor $riskColor
            
            # Ask if user wants to execute the command
            if ($result.RiskLevel -lt 3) {
                Write-Host "`nDo you want to execute this command? (yes/no): " -ForegroundColor Yellow -NoNewline
                $execute = Read-Host
                
                if ($execute -eq 'yes') {
                    # Ask for working directory
                    Write-Host "Enter working directory (press Enter for current): " -ForegroundColor Yellow -NoNewline
                    $workingDir = Read-Host
                    
                    if ([string]::IsNullOrWhiteSpace($workingDir)) {
                        $workingDir = (Get-Location).Path
                    }
                    
                    # Execute the command
                    Write-Host "`nExecuting command..." -ForegroundColor Cyan
                    $execResult = Invoke-SafeCommand -Command $result.command -WorkingDirectory $workingDir
                    
                    # Display execution results
                    Write-Host "`nExecution Result:" -ForegroundColor Cyan
                    if ($execResult.ExecutionSuccessful) {
                        Write-Host "Success (Exit Code: $($execResult.ExitCode))" -ForegroundColor Green
                        Write-Host "Execution Time: $($execResult.ExecutionTime) seconds" -ForegroundColor Gray
                        
                        Write-Host "`nOutput:" -ForegroundColor White
                        Write-Host $execResult.Stdout -ForegroundColor Gray
                    } else {
                        Write-Host "Failed (Exit Code: $($execResult.ExitCode))" -ForegroundColor Red
                        
                        if ($execResult.Error) {
                            Write-Host "`nError:" -ForegroundColor Red
                            Write-Host $execResult.Error -ForegroundColor Red
                        }
                        
                        if ($execResult.Stderr) {
                            Write-Host "`nStandard Error:" -ForegroundColor Red
                            Write-Host $execResult.Stderr -ForegroundColor Red
                        }
                    }
                    
                    # Show watermark for audit
                    Write-Host "`nCommand Watermark:" -ForegroundColor Cyan
                    Write-Host "DNA Signature: $($execResult.Watermark.DnaSignature)" -ForegroundColor Gray
                    Write-Host "Timestamp: $($execResult.Watermark.Timestamp)" -ForegroundColor Gray
                    Write-Host "Visual Code: $($execResult.Watermark.VisualCode)" -ForegroundColor Gray
                }
            } else {
                Write-Host "`nThis high-risk command cannot be executed automatically." -ForegroundColor Red
            }
            
        } catch {
            Write-Host "Error: $_" -ForegroundColor Red
        }
        
        Write-Host "`n" + "-" * 80 + "`n" -ForegroundColor DarkGray
    }
    
    Write-Host "`nThank you for using PowerShell Command Translator Demo" -ForegroundColor Cyan
}

# If script is run directly, start the demo
if ($MyInvocation.InvocationName -ne '.') {
    Start-PowerShellTranslatorDemo
}

# Export functions for module use
Export-ModuleMember -Function Initialize-PowerShellTranslator, ConvertTo-PowerShellCommand, Invoke-SafeCommand, Start-PowerShellTranslatorDemo
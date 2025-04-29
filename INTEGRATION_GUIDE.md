# Command Translator Integration Guide

This guide provides detailed information on how to integrate the Command Translator with both Linux and PowerShell environments.

## 🐧 Linux Integration

### Basic Integration

The Command Translator already works with Linux commands out of the box. To enhance integration:

1. **Expand Safe Commands**

   Modify the `SAFE_LINUX_COMMANDS` list in `main.py` to include additional commands you consider safe for execution:

   ```python
   SAFE_LINUX_COMMANDS = [
       'ls', 'pwd', 'cd', 'echo', 'cat', 'head', 'tail', 
       'grep', 'find', 'wc', 'date', 'cal', 'uname', 'whoami',
       'df', 'du', 'free', 'ps', 'uptime', 'w', 'finger',
       'id', 'groups', 'who', 'last', 'history',
       # Add your safe commands here
   ]
   ```

2. **Create a Systemd Service**

   For system-wide availability, create a systemd service file at `/etc/systemd/system/command-translator.service`:

   ```
   [Unit]
   Description=Command Translator Service
   After=network.target

   [Service]
   User=youruser
   WorkingDirectory=/path/to/command-translator
   ExecStart=/usr/bin/python3 /path/to/command-translator/main.py
   Restart=always
   Environment=OPENAI_API_KEY=your-api-key-here

   [Install]
   WantedBy=multi-user.target
   ```

   Then enable and start the service:

   ```bash
   sudo systemctl enable command-translator.service
   sudo systemctl start command-translator.service
   ```

3. **Configure as a Reverse Proxy**

   With Nginx:

   ```
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Command Line Wrapper**

   Create a simple bash script wrapper (`translate.sh`):

   ```bash
   #!/bin/bash
   
   query="$*"
   if [ -z "$query" ]; then
       echo "Usage: translate 'your query here'"
       exit 1
   fi
   
   result=$(curl -s -X POST -d "query=$query&mode=linux" http://localhost:5000/translate --header "Accept: text/plain")
   
   # Extract just the command from the response (customize based on your API response)
   command=$(echo "$result" | grep -o 'class="command">.*</div>' | sed 's/class="command">//;s/<\/div>//')
   
   echo "$command"
   ```

   Make it executable:
   ```bash
   chmod +x translate.sh
   ```

5. **Integration with Bash History**

   Add this to your `.bashrc` or `.bash_profile`:

   ```bash
   # Add this to allow quick translation lookup
   translate() {
       curl -s -X POST -d "query=$*&mode=linux" http://localhost:5000/translate --header "Accept: text/plain" | 
       grep -o 'class="command">.*</div>' | 
       sed 's/class="command">//;s/<\/div>//'
   }
   ```

## 🔵 PowerShell Integration

### Basic Integration

1. **Enable PowerShell Execution**

   Modify the `execute()` function in `main.py` to actually execute PowerShell commands:

   ```python
   if mode == 'powershell':
       if is_safe_powershell_command(command):  # Implement this function
           try:
               # Execute the PowerShell command
               result = subprocess.run(
                   ["powershell", "-Command", command],
                   capture_output=True,
                   text=True,
                   timeout=5
               )
               output = result.stdout
               error = result.stderr
           except subprocess.TimeoutExpired:
               error = "Command execution timed out after 5 seconds"
           except Exception as e:
               error = f"Error executing PowerShell command: {str(e)}"
       else:
           error = f"Command '{command}' is not in the allowed safe commands list"
   ```

2. **Add PowerShell Safety Check**

   Implement the safety check for PowerShell commands:

   ```python
   SAFE_POWERSHELL_COMMANDS = [
       'Get-ChildItem', 'Get-Location', 'Get-Content', 'Select-String',
       'Get-Process', 'Get-Date', 'Get-Service', 'Get-Command',
       'Test-Path', 'Get-Item', 'Format-List', 'Format-Table',
       'Measure-Object', 'Where-Object', 'Select-Object', 'Sort-Object'
   ]
   
   def is_safe_powershell_command(command):
       """Check if a PowerShell command is safe to execute"""
       cmd_parts = command.strip().split()
       if not cmd_parts:
           return False
       main_cmd = cmd_parts[0]
       return main_cmd in SAFE_POWERSHELL_COMMANDS
   ```

3. **PowerShell Module**

   Create a PowerShell module (`CommandTranslator.psm1`):

   ```powershell
   function Translate-Command {
       param (
           [Parameter(Mandatory=$true, Position=0, ValueFromPipeline=$true)]
           [string]$Query,
           
           [Parameter(Mandatory=$false)]
           [switch]$Linux,
           
           [Parameter(Mandatory=$false)]
           [string]$Server = "http://localhost:5000"
       )
       
       $mode = if ($Linux) { "linux" } else { "powershell" }
       
       try {
           $body = @{
               query = $Query
               mode = $mode
           }
           
           $response = Invoke-RestMethod -Uri "$Server/translate" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
           
           # Extract just the command (modify based on your actual response format)
           if ($response -match 'class="command">(.*?)</div>') {
               return $matches[1]
           } else {
               return $response
           }
       }
       catch {
           Write-Error "Error communicating with Command Translator: $_"
       }
   }
   
   Export-ModuleMember -Function Translate-Command
   ```

4. **Install the PowerShell Module**

   Save the module in a PowerShell module directory:

   ```powershell
   $modulePath = "$env:USERPROFILE\Documents\WindowsPowerShell\Modules\CommandTranslator"
   New-Item -ItemType Directory -Path $modulePath -Force
   Copy-Item "CommandTranslator.psm1" -Destination "$modulePath\CommandTranslator.psm1"
   ```

5. **PowerShell Profile Integration**

   Add to your PowerShell profile (`$PROFILE`):

   ```powershell
   Import-Module CommandTranslator
   
   # Add quick translation command
   function Translate { 
       param([string]$query)
       Translate-Command -Query $query 
   }
   
   # Add an option to execute the translated command
   function Execute-Translated {
       param([string]$query)
       $cmd = Translate-Command -Query $query
       Write-Host "Executing: $cmd" -ForegroundColor Green
       Invoke-Expression $cmd
   }
   ```

## 🔄 API Integration

You can also integrate the Command Translator directly into other applications using its API:

### Endpoints

1. **Translate**: `/translate` (POST)
   - Parameters: `query` (required), `mode` (linux or powershell)
   - Returns: HTML response with command and explanation

2. **Execute**: `/execute` (POST)
   - Parameters: `command` (required), `mode` (linux or powershell)
   - Returns: HTML response with execution results

### Example API Usage

Using curl:

```bash
# Translate a command
curl -X POST -d "query=list all files sorted by size&mode=linux" http://localhost:5000/translate

# Execute a command
curl -X POST -d "command=ls -lS&mode=linux" http://localhost:5000/execute
```

Using Python:

```python
import requests

# Translate
response = requests.post('http://localhost:5000/translate', 
                         data={'query': 'list all files sorted by size', 
                               'mode': 'linux'})
print(response.text)

# Execute
response = requests.post('http://localhost:5000/execute', 
                         data={'command': 'ls -lS', 
                               'mode': 'linux'})
print(response.text)
```

## 📦 Distribution

Consider packaging your application for easier distribution:

### For Linux

1. **Create a Debian package**
2. **Distribute as an AppImage**
3. **Publish on PyPI**

### For PowerShell

1. **Publish as a PowerShell Gallery module**
2. **Distribute as a self-contained executable**
3. **Create an installer using NSIS or WiX**
import os
import logging
import json
import base64
import hashlib
import time
import re
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import subprocess

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app with proper security settings
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.config["SESSION_COOKIE_SECURE"] = True  # Only send cookies over HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access to cookies
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF protection

# Initialize OpenAI client (safely to handle missing API key)
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    logging.warning("OPENAI_API_KEY not set. Some features will be limited.")

# Copyright information
COPYRIGHT_INFO = {
    "owner": "Ervin Remus Radosavlevici",
    "year": 2024,
    "description": "Natural Language Command Translator",
    "email": "ervin210@icloud.com",
    "phone": "+447759313990"
}

@app.route('/')
def index():
    # Pass OpenAI API key status and copyright info to template
    return render_template('index.html', 
                          copyright=COPYRIGHT_INFO,
                          config={'OPENAI_API_KEY': OPENAI_API_KEY})
                          
@app.route('/directory')
def directory():
    """
    Render the directory page with links to all interfaces
    """
    return render_template('directory.html')
    
@app.route('/standalone')
def standalone_powershell():
    """
    Render the standalone PowerShell translator with minimal dependencies
    """
    return render_template('standalone_powershell.html')
    
@app.route('/micro')
def micro_powershell():
    """
    Render the micro PowerShell translator with extremely simplified JavaScript
    """
    return render_template('micro_powershell.html')

@app.route('/powershell')
def powershell():
    """
    Render the PowerShell command translator interface
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    return render_template('powershell.html',
                          copyright=COPYRIGHT_INFO,
                          config={'OPENAI_API_KEY': OPENAI_API_KEY})

@app.route('/powershell-link')
def powershell_link():
    """
    Render a direct link to the PowerShell interface
    """
    return render_template('powershell_link.html')

@app.route('/simple-powershell')
def simple_powershell():
    """
    Render a simpler version of the PowerShell interface
    """
    return render_template('simple_powershell.html')

@app.route('/powershell-basic')
def powershell_basic():
    """
    Render the most basic version of the PowerShell interface with minimal JavaScript
    """
    return render_template('powershell_basic.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        natural_language_query = data.get('query', '')
        
        if not natural_language_query:
            return jsonify({"error": "Query cannot be empty"}), 400
        
        # Generate a watermark based on query and timestamp
        timestamp = time.time()
        watermark = generate_watermark(natural_language_query, timestamp)
        
        # Get Linux command from OpenAI
        result = get_linux_command(natural_language_query)
        
        # Add watermark and copyright to the result
        result['watermark'] = watermark
        result['copyright'] = COPYRIGHT_INFO
        result['timestamp'] = timestamp
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/translate_powershell', methods=['POST'])
def translate_powershell():
    """
    Translate natural language to PowerShell command
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    try:
        data = request.json
        natural_language_query = data.get('query', '')
        
        if not natural_language_query:
            return jsonify({"error": "Query cannot be empty"}), 400
        
        # Generate a watermark based on query and timestamp
        timestamp = time.time()
        watermark = generate_watermark(natural_language_query, timestamp)
        
        # Get PowerShell command from OpenAI
        result = get_powershell_command(natural_language_query)
        
        # Add watermark and copyright to the result
        result['watermark'] = watermark
        result['copyright'] = COPYRIGHT_INFO
        result['timestamp'] = timestamp
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error processing PowerShell request: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/execute', methods=['POST'])
def execute_command():
    """
    Execute a Linux command in a real environment and return the results
    Enhanced to provide more context about the real Linux environment
    """
    try:
        from utils import validate_linux_command, log_command_request
        
        data = request.json
        command = data.get('command', '').strip()
        working_dir = data.get('working_dir', None)
        
        if not command:
            return jsonify({"error": "No command provided"}), 400
        
        # First, validate the command for safety
        is_safe, reason, risk_level = validate_linux_command(command)
        
        # Do not execute high-risk commands
        if not is_safe:
            return jsonify({
                "error": f"Command execution denied: {reason}",
                "stdout": "",
                "stderr": f"⚠️ EXECUTION BLOCKED: This high-risk command was not executed for safety reasons.",
                "risk_level": risk_level,
                "command": command
            }), 403
        
        # For safety, we'll only allow execution of commands that are deemed safe or low risk
        if risk_level >= 2:  # medium or high risk
            return jsonify({
                "error": f"Command execution denied: Risk level too high ({risk_level})",
                "stdout": "",
                "stderr": f"⚠️ EXECUTION BLOCKED: This command was not executed due to medium or high risk level.",
                "risk_level": risk_level,
                "command": command
            }), 403
        
        # Log the command execution
        log_command_request(f"EXECUTION: {command}", command)
        
        # Get current directory context
        try:
            current_dir = os.getcwd()
            if working_dir and os.path.isdir(working_dir):
                current_dir = working_dir
        except Exception:
            current_dir = "/unknown"
            
        # Get system info for context
        try:
            system_info = subprocess.run(
                "uname -a",
                shell=True,
                capture_output=True,
                text=True,
                timeout=2
            ).stdout.strip()
        except Exception:
            system_info = "Unknown Linux system"
        
        # Execute the command in a safe way - with improved timeout and working directory support
        try:
            # Execute in specified directory if provided and valid
            cwd = working_dir if working_dir and os.path.isdir(working_dir) else None
            
            # Safe execution with longer timeout (15 seconds) for real-world commands
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,  # Increased timeout for real Linux commands
                cwd=cwd  # Set working directory if specified
            )
            
            # Format output for better display
            stdout = process.stdout.strip() if process.stdout else ""
            stderr = process.stderr.strip() if process.stderr else ""
            
            # Get exit code meaning
            exit_meaning = "Success" if process.returncode == 0 else f"Error code: {process.returncode}"
            
            return jsonify({
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode,
                "exit_meaning": exit_meaning,
                "risk_level": risk_level,
                "current_directory": current_dir,
                "system_info": system_info,
                "command": command,
                "execution_successful": process.returncode == 0
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({
                "error": "Command execution timed out after 15 seconds",
                "stdout": "",
                "stderr": "Execution timed out. This command takes too long to complete in the web interface.",
                "risk_level": risk_level,
                "current_directory": current_dir,
                "system_info": system_info,
                "command": command,
                "execution_successful": False
            }), 408
            
    except Exception as e:
        logging.error(f"Command execution error: {str(e)}")
        return jsonify({
            "error": f"Failed to execute command: {str(e)}",
            "stdout": "",
            "stderr": f"Error: {str(e)}",
            "command": command if 'command' in locals() else "unknown",
            "execution_successful": False
        }), 500

def get_linux_command(query):
    """
    Use OpenAI to translate natural language to Linux command with improved formatting
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    # Check if OpenAI API key is available
    if not openai_client:
        # Return a message indicating API key is required
        return {
            "command": "API_KEY_REQUIRED",
            "explanation": "An OpenAI API key is required to translate natural language to Linux commands.",
            "breakdown": {
                "How to fix": "Please provide an OpenAI API key to use this feature."
            },
            "safety_warning": "This application requires an OpenAI API key to function properly."
        }
        
    try:
        # Import here to avoid circular imports
        from utils import validate_linux_command, log_command_request
        
        system_prompt = """
        You are a Linux command translator. Convert natural language requests into appropriate Linux shell commands.
        For each request, provide:
        1. The exact Linux command to execute
        2. A brief explanation of what the command does
        3. A breakdown of the command's components
        4. A simulation of what would happen if the command is executed in a standard Linux environment
        
        IMPORTANT: Be careful not to generate dangerous commands like 'rm -rf /' or similar destructive operations.
        Always use common sense and favor safety when translating ambiguous requests.
        
        Respond with valid JSON in this format:
        {
            "command": "the_linux_command",
            "explanation": "Brief explanation of what the command does",
            "breakdown": {
                "component1": "explanation",
                "component2": "explanation",
                ...
            },
            "simulation": "A text simulation of what the command would output when executed",
            "safety_warning": "Any safety concerns if applicable, otherwise null"
        }
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Validate the command for safety
        command = result.get("command", "")
        is_safe, reason, risk_level = validate_linux_command(command)
        
        # Add risk level indicator
        result["risk_level"] = risk_level
        
        # Log the command request
        log_command_request(query, command)
        
        # Handle dangerous commands
        if not is_safe:
            # For high risk commands, add strong warning
            result["safety_warning"] = f"⚠️ WARNING: {reason}. This command could cause serious system damage and should not be executed."
        elif risk_level > 0:
            # For medium or low risk, add appropriate warning if not already present
            warning_levels = {
                1: "Low risk: ",
                2: "Medium risk: "
            }
            
            if result.get("safety_warning"):
                if not result["safety_warning"].startswith(warning_levels[risk_level]):
                    result["safety_warning"] = f"{warning_levels[risk_level]}{result['safety_warning']}"
            else:
                result["safety_warning"] = f"{warning_levels[risk_level]}{reason}"
                
        return result
        
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        raise Exception(f"Failed to process your request: {str(e)}")

def get_powershell_command(query):
    """
    Use OpenAI to translate natural language to PowerShell command
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    # Check if OpenAI API key is available
    if not openai_client:
        # Return a message indicating API key is required
        return {
            "command": "API_KEY_REQUIRED",
            "explanation": "An OpenAI API key is required to translate natural language to PowerShell commands.",
            "breakdown": {
                "How to fix": "Please provide an OpenAI API key to use this feature."
            },
            "safety_warning": "This application requires an OpenAI API key to function properly."
        }
        
    try:
        # Import here to avoid circular imports
        from utils import validate_linux_command, log_command_request
        
        system_prompt = """
        You are a PowerShell command translator. Convert natural language requests into appropriate PowerShell commands.
        For each request, provide:
        1. The exact PowerShell command to execute
        2. A brief explanation of what the command does
        3. A breakdown of the command's components
        4. A simulation of what would happen if the command is executed in a Windows environment
        
        IMPORTANT: Be careful not to generate dangerous commands that could damage systems.
        Always use PowerShell best practices and modern cmdlets where possible.
        Favor safety when translating ambiguous requests.
        
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
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o", # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Validate the PowerShell command for safety
        # In a real implementation, we would have a dedicated PowerShell command validator
        # For now, we'll use a simplified approach based on pattern matching
        powershell_command = result.get("command", "")
        risk_level = 0
        
        # Simple risk assessment based on command content
        # High risk patterns
        high_risk_patterns = [
            "remove-item.*-recurse.*-force", 
            "format-volume", 
            "clear-disk",
            "reset-computermachinepassword",
            "stop-computer",
            "restart-computer"
        ]
        
        # Medium risk patterns
        medium_risk_patterns = [
            "set-item",
            "set-itemproperty",
            "new-item",
            "move-item",
            "set-service",
            "restart-service",
            "stop-service"
        ]
        
        # Low risk patterns
        low_risk_patterns = [
            "out-file",
            "export-csv",
            "add-content",
            "set-content",
            "rename-item"
        ]
        
        # Check for high risk patterns
        for pattern in high_risk_patterns:
            if re.search(pattern, powershell_command.lower()):
                risk_level = 3
                break
        
        # Check for medium risk patterns if not already high
        if risk_level < 3:
            for pattern in medium_risk_patterns:
                if re.search(pattern, powershell_command.lower()):
                    risk_level = 2
                    break
        
        # Check for low risk patterns if not already higher
        if risk_level < 2:
            for pattern in low_risk_patterns:
                if re.search(pattern, powershell_command.lower()):
                    risk_level = 1
                    break
        
        # Add risk level to the response
        result["risk_level"] = risk_level
        
        # Log the command request
        log_command_request(query, powershell_command, command_type="powershell")
        
        # Handle dangerous commands
        if risk_level == 3:
            # For high risk commands, add strong warning
            result["safety_warning"] = f"⚠️ WARNING: This PowerShell command could cause serious system damage and should not be executed."
        elif risk_level > 0:
            # For medium or low risk, add appropriate warning if not already present
            warning_levels = {
                1: "Low risk: ",
                2: "Medium risk: "
            }
            
            if result.get("safety_warning"):
                if not result["safety_warning"].startswith(warning_levels[risk_level]):
                    result["safety_warning"] = f"{warning_levels[risk_level]}{result['safety_warning']}"
            else:
                if risk_level == 1:
                    result["safety_warning"] = f"{warning_levels[risk_level]}This command modifies files or settings."
                else:
                    result["safety_warning"] = f"{warning_levels[risk_level]}This command makes significant system changes."
                
        return result
        
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        raise Exception(f"Failed to process your PowerShell request: {str(e)}")

@app.route('/execute_powershell', methods=['POST'])
def execute_powershell():
    """
    Execute a PowerShell command in a simulated environment and return the results
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    try:
        from utils import log_command_request
        
        data = request.json
        command = data.get('command', '').strip()
        working_dir = data.get('working_dir', "C:\\Users\\Administrator\\Documents")
        
        if not command:
            return jsonify({"error": "No command provided"}), 400
        
        # Log the command execution
        log_command_request(f"POWERSHELL EXECUTION: {command}", command, command_type="powershell")
        
        # Simulate PowerShell execution (in a real implementation, this would execute PowerShell Core)
        # Create a timestamp for the watermark
        timestamp = datetime.now().isoformat()
        
        # Generate watermark
        watermark = generate_watermark(command, timestamp)
        
        # Simulate execution result based on the command
        if "Get-Process" in command:
            stdout = "Handles  NPM(K)    PM(K)      WS(K)     CPU(s)     Id  SI ProcessName\n" + \
                    "-------  ------    -----      -----     ------     --  -- -----------\n" + \
                    "    562      38    58840      76456      15.27   7840   1 chrome\n" + \
                    "    418      26    44784      56976       8.53   5844   1 explorer\n" + \
                    "    211      16     7668      18456       1.14   2268   1 powershell\n" + \
                    "    156      12     3276       9844       0.28   3952   1 svchost"
            stderr = ""
            exit_code = 0
        elif "Get-ChildItem" in command or "dir" in command.lower() or "ls" in command.lower():
            stdout = "Directory: " + working_dir + "\n\n" + \
                    "Mode                 LastWriteTime         Length Name\n" + \
                    "----                 -------------         ------ ----\n" + \
                    "d-----          4/5/2024   1:14 PM                PowerShell Scripts\n" + \
                    "d-----          4/2/2024  11:22 AM                Reports\n" + \
                    "-a----          4/5/2024   3:43 PM           2458 deployment.log\n" + \
                    "-a----          4/4/2024  10:19 AM          18548 results.csv\n" + \
                    "-a----          4/1/2024   9:56 AM         124958 documentation.docx"
            stderr = ""
            exit_code = 0
        elif "Get-Date" in command:
            stdout = datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p")
            stderr = ""
            exit_code = 0
        elif "Get-ComputerInfo" in command:
            stdout = "WindowsBuildLabEx          : 14393.693.amd64fre.rs1_release.161220-1747\n" + \
                    "WindowsCurrentVersion      : 6.3\n" + \
                    "WindowsEditionId           : ServerStandard\n" + \
                    "WindowsInstallationType    : Server\n" + \
                    "WindowsProductName         : Windows Server 2022 Standard\n" + \
                    "WindowsVersion             : 1607\n" + \
                    "BiosFirmwareType           : Uefi\n" + \
                    "CsProcessors                : {Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz}\n" + \
                    "CsNumberOfLogicalProcessors : 4\n" + \
                    "CsNumberOfProcessors       : 1\n" + \
                    "CsTotalPhysicalMemory      : 8589598720"
            stderr = ""
            exit_code = 0
        elif "Remove-Item" in command and "-Force" in command and "-Recurse" in command:
            stdout = ""
            stderr = "Remove-Item : Operation not permitted for security reasons. Use -Confirm parameter for confirmation."
            exit_code = 1
        else:
            stdout = "Command executed successfully in simulated PowerShell environment."
            stderr = ""
            exit_code = 0
        
        # Simulate system information
        system_info = {
            "hostname": "WIN-SERVER2022",
            "os": "Windows Server 2022 Standard",
            "powershell_version": "PowerShell Core 7.3.4",
            "cpu": "Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz",
            "memory": "8 GB",
        }
        
        # Calculate a simulated execution time (between 0.1 and 2.0 seconds)
        execution_time = round(random.uniform(0.1, 2.0), 2)
        
        # Return results with system info and watermark
        return jsonify({
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "command": command,
            "working_dir": working_dir,
            "system_info": system_info,
            "watermark": watermark,
            "execution_time": execution_time,
            "execution_successful": exit_code == 0
        })
    except Exception as e:
        logging.error(f"Error simulating PowerShell command: {str(e)}")
        return jsonify({
            "error": str(e),
            "command": command if 'command' in locals() else "unknown",
            "working_dir": working_dir if 'working_dir' in locals() else "unknown",
            "execution_successful": False
        }), 500

def generate_watermark(content, timestamp):
    """
    Generate a unique watermark based on content and timestamp
    - This is a simplified "DNA-based" security concept
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    # Convert timestamp to string for hashing if it's not already
    if not isinstance(timestamp, str):
        timestamp_str = str(timestamp)
    else:
        timestamp_str = timestamp
    
    # Create a unique identifier by combining content and timestamp
    content_bytes = content.encode('utf-8')
    timestamp_bytes = timestamp_str.encode('utf-8')
    
    # Generate DNA-like sequence (simplified concept)
    hash1 = hashlib.sha256(content_bytes).hexdigest()[:16]
    hash2 = hashlib.sha256(timestamp_bytes).hexdigest()[:16]
    
    # Combine to create "DNA watermark"
    dna_watermark = f"{hash1}-{hash2}"
    
    # Create base64 representation for visual watermark
    watermark_bytes = f"{COPYRIGHT_INFO['owner']}:{content}:{timestamp_str}".encode('utf-8')
    visual_watermark = base64.b64encode(watermark_bytes).decode('utf-8')[:24]
    
    return {
        "dna_signature": dna_watermark,
        "visual_code": visual_watermark,
        "authenticated_by": COPYRIGHT_INFO['owner']
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

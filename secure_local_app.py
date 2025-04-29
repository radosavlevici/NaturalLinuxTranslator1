import os
import json
import subprocess
import shlex
import hashlib
from datetime import datetime
from flask import Flask, request, render_template, session, redirect, url_for, flash
from utils import validate_linux_command, sanitize_input, log_command_request, create_security_signature

# Create a Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "a_secure_key_for_development")

# Get OpenAI API key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        print("OpenAI Python package not installed")
        openai_client = None
else:
    print("No OpenAI API key found")
    openai_client = None

# Safe commands list for Linux - these are considered safe to execute
SAFE_LINUX_COMMANDS = [
    'ls', 'pwd', 'cd', 'echo', 'cat', 'head', 'tail', 
    'grep', 'find', 'wc', 'date', 'cal', 'uname', 'whoami',
    'df', 'du', 'free', 'ps', 'top', 'uptime', 'w', 'finger',
    'id', 'groups', 'who', 'last', 'history'
]

# Function to validate if a Linux command is safe
def is_safe_linux_command(command):
    """Check if a Linux command is safe to execute"""
    cmd = shlex.split(command)[0] if command else ""
    return cmd in SAFE_LINUX_COMMANDS

@app.route('/')
def home():
    watermark = create_security_signature("Command Translator")
    return f"""
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Command Translator - Natural Language to Terminal Commands</title>
        <!-- Bootstrap CSS -->
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{
                padding-top: 80px;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            .footer {{
                margin-top: auto;
                padding: 20px 0;
            }}
            .command-display {{
                font-family: monospace;
                background-color: var(--bs-dark);
                border: 1px solid var(--bs-gray-600);
                padding: 15px;
                border-radius: 5px;
                white-space: pre-wrap;
                overflow-x: auto;
            }}
            .explanation {{
                background-color: var(--bs-gray-800);
                padding: 15px;
                border-radius: 5px;
                margin-top: 15px;
            }}
            .watermark-label {{
                font-size: 0.7rem;
                color: var(--bs-gray-600);
                text-align: center;
                margin-top: 15px;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-terminal me-2"></i>Command Translator
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link active" href="/">Home</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <div class="container mb-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h4 class="mb-0"><i class="fas fa-language me-2"></i>Natural Language to Command</h4>
                        </div>
                        <div class="card-body">
                            <form action="/translate" method="post">
                                <div class="mb-3">
                                    <label for="query" class="form-label">What would you like to do?</label>
                                    <textarea class="form-control" id="query" name="query" rows="3" 
                                        placeholder="Ex: List all files sorted by size, Show system memory usage, Find all text files containing 'error'"></textarea>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check form-check-inline">
                                        <input class="form-check-input" type="radio" name="mode" id="linux" value="linux" checked>
                                        <label class="form-check-label" for="linux">
                                            <i class="fab fa-linux me-1"></i>Linux
                                        </label>
                                    </div>
                                    <div class="form-check form-check-inline">
                                        <input class="form-check-input" type="radio" name="mode" id="powershell" value="powershell">
                                        <label class="form-check-label" for="powershell">
                                            <i class="fab fa-windows me-1"></i>PowerShell
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="d-grid gap-2">
                                    <button type="submit" class="btn btn-primary">
                                        <i class="fas fa-sync-alt me-2"></i>Translate to Command
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>About Command Translator</h5>
                        </div>
                        <div class="card-body">
                            <p>Command Translator helps you convert natural language descriptions into terminal commands.</p>
                            <p>Simply describe what you want to do in plain English, select your preferred terminal environment, and get the exact command to run.</p>
                            <ul>
                                <li>Supports both Linux and PowerShell commands</li>
                                <li>Provides explanations of how commands work</li>
                                <li>Validates commands for safety</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="footer bg-dark text-light">
            <div class="container">
                <div class="row">
                    <div class="col-md-6">
                        <p><i class="fas fa-code me-2"></i>Command Translator</p>
                        <p class="small">Copyright &copy; 2024 Command Translator</p>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <p class="small watermark-label">Security Token: {watermark}</p>
                    </div>
                </div>
            </div>
        </footer>

        <!-- JavaScript Bundle with Popper -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@app.route('/translate', methods=['POST'])
def translate():
    query = request.form.get('query', '')
    mode = request.form.get('mode', 'linux')
    
    if not query:
        return "Error: No query provided"
    
    # Sanitize input
    clean_query = sanitize_input(query)
    
    if mode == 'powershell':
        result = get_powershell_command(clean_query)
    else:
        result = get_linux_command(clean_query)
    
    command = result.get('command', 'Error generating command')
    explanation = result.get('explanation', '')
    
    # Create security watermark
    watermark = create_security_signature(f"{clean_query}|{command}|{datetime.utcnow().isoformat()}")
    
    # Log the request
    log_command_request(clean_query, command, request.remote_addr, mode)
    
    # If command is executable, validate it
    is_safe = False
    risk_level = 3
    safety_message = ""
    
    if mode == 'linux':
        is_safe, safety_message, risk_level = validate_linux_command(command)
    
    return f"""
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Command Translation Result</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{
                padding-top: 80px;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            .footer {{
                margin-top: auto;
                padding: 20px 0;
            }}
            .command-display {{
                font-family: monospace;
                background-color: var(--bs-dark);
                border: 1px solid var(--bs-gray-600);
                padding: 15px;
                border-radius: 5px;
                white-space: pre-wrap;
                overflow-x: auto;
            }}
            .explanation {{
                background-color: var(--bs-gray-800);
                padding: 15px;
                border-radius: 5px;
                margin-top: 15px;
            }}
            .watermark-label {{
                font-size: 0.7rem;
                color: var(--bs-gray-600);
                text-align: center;
                margin-top: 15px;
            }}
            .security-badge {{
                display: inline-block;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 0.8rem;
                margin-bottom: 10px;
            }}
            .risk-0 {{ background-color: var(--bs-success); }}
            .risk-1 {{ background-color: var(--bs-info); }}
            .risk-2 {{ background-color: var(--bs-warning); color: var(--bs-dark); }}
            .risk-3 {{ background-color: var(--bs-danger); }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-terminal me-2"></i>Command Translator
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/">Home</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <div class="container mb-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                            <h4 class="mb-0"><i class="fas fa-code me-2"></i>Command Result</h4>
                            <span>
                                <i class="fas {{'fa-linux' if mode == 'linux' else 'fa-windows'}} me-1"></i>
                                {mode.capitalize()}
                            </span>
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">Your Query:</h5>
                            <p class="card-text">{clean_query}</p>
                            
                            <hr>
                            
                            <h5 class="card-title">Command:</h5>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <div>
                                    {f'<span class="security-badge risk-{risk_level}"><i class="fas fa-shield-alt me-1"></i>{"Safe" if is_safe else "Unsafe"} Command</span>' if mode == 'linux' else ''}
                                </div>
                                <button class="btn btn-sm btn-secondary" onclick="copyToClipboard()">
                                    <i class="fas fa-copy me-1"></i>Copy
                                </button>
                            </div>
                            <div class="command-display" id="command-text">{command}</div>
                            
                            {f'<p class="text-muted small mt-1">{safety_message}</p>' if mode == 'linux' else ''}
                            
                            <h5 class="card-title mt-4">Explanation:</h5>
                            <div class="explanation">
                                {explanation}
                            </div>
                            
                            <div class="mt-4">
                                <a href="/" class="btn btn-primary">
                                    <i class="fas fa-arrow-left me-2"></i>New Translation
                                </a>
                                
                                {f'''
                                <form action="/api/translate" method="post" class="d-inline-block ms-2">
                                    <input type="hidden" name="command" value="{command}">
                                    <input type="hidden" name="mode" value="{mode}">
                                    <button type="submit" class="btn btn-success" {"disabled" if not is_safe and mode == 'linux' else ""}>
                                        <i class="fas fa-play me-2"></i>Execute Command
                                    </button>
                                </form>
                                ''' if is_safe or mode == 'powershell' else ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="footer bg-dark text-light">
            <div class="container">
                <div class="row">
                    <div class="col-md-6">
                        <p><i class="fas fa-code me-2"></i>Command Translator</p>
                        <p class="small">Copyright &copy; 2024 Command Translator</p>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <p class="small watermark-label">Security Token: {watermark}</p>
                    </div>
                </div>
            </div>
        </footer>
        
        <script>
        function copyToClipboard() {{
            const commandText = document.getElementById('command-text');
            const textArea = document.createElement('textarea');
            textArea.value = commandText.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            // Show a temporary "Copied!" message
            const btn = event.currentTarget;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
            setTimeout(() => {{
                btn.innerHTML = originalText;
            }}, 2000);
        }}
        </script>

        <!-- JavaScript Bundle with Popper -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@app.route('/api/translate', methods=['POST'])
def api_translate():
    query = request.form.get('query', '')
    mode = request.form.get('mode', 'linux')
    command = request.form.get('command', '')
    
    # If command is provided directly, use it, otherwise translate query
    if not command and query:
        # Sanitize input
        clean_query = sanitize_input(query)
        
        if mode == 'powershell':
            result = get_powershell_command(clean_query)
        else:
            result = get_linux_command(clean_query)
        
        command = result.get('command', '')
    
    # Execute the command
    output = "Command execution not available in this environment"
    error = ""
    execution_success = False
    
    if command:
        if mode == 'linux':
            # Validate Linux command
            is_safe, reason, risk_level = validate_linux_command(command)
            
            # Only execute safe commands
            if is_safe and risk_level < 2:  # Only execute safe or low-risk commands
                try:
                    # Execute the command with timeout
                    result = subprocess.run(
                        command, 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        timeout=5
                    )
                    output = result.stdout
                    error = result.stderr
                    execution_success = result.returncode == 0
                except subprocess.TimeoutExpired:
                    error = "Command execution timed out after 5 seconds"
                except Exception as e:
                    error = f"Error executing command: {str(e)}"
            else:
                error = f"Command not executed for security reasons: {reason}"
        else:
            # PowerShell execution simulation
            output = f"PowerShell execution simulated for: {command}"
            error = "Note: Real PowerShell execution is not available in this environment"
            execution_success = True
    
    # Create response data
    response_data = {
        "success": True if command else False,
        "command": command,
        "output": output,
        "error": error,
        "execution_success": execution_success,
        "mode": mode,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Generate security watermark
    watermark = create_security_signature(f"{command}|{output}|{datetime.utcnow().isoformat()}")
    response_data["security_signature"] = watermark
    
    # Return the JSON response
    return f"""
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Command Execution Result</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{
                padding-top: 80px;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            .footer {{
                margin-top: auto;
                padding: 20px 0;
            }}
            .command-display, .output-display {{
                font-family: monospace;
                background-color: var(--bs-dark);
                border: 1px solid var(--bs-gray-600);
                padding: 15px;
                border-radius: 5px;
                white-space: pre-wrap;
                overflow-x: auto;
                max-height: 300px;
                overflow-y: auto;
            }}
            .watermark-label {{
                font-size: 0.7rem;
                color: var(--bs-gray-600);
                text-align: center;
                margin-top: 15px;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-terminal me-2"></i>Command Translator
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/">Home</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <div class="container mb-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
                            <h4 class="mb-0"><i class="fas fa-play me-2"></i>Execution Result</h4>
                            <span>
                                <i class="fas {{'fa-linux' if mode == 'linux' else 'fa-windows'}} me-1"></i>
                                {mode.capitalize()}
                            </span>
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">Executed Command:</h5>
                            <div class="command-display">{command}</div>
                            
                            <h5 class="card-title mt-4">
                                Output:
                                {f'<span class="text-success ms-2"><i class="fas fa-check-circle"></i> Success</span>' if execution_success else f'<span class="text-danger ms-2"><i class="fas fa-times-circle"></i> Failed</span>'}
                            </h5>
                            <div class="output-display">{output if output else "No output"}</div>
                            
                            {f'<h5 class="card-title mt-4">Error:</h5><div class="output-display text-danger">{error}</div>' if error else ''}
                            
                            <div class="mt-4">
                                <a href="/" class="btn btn-primary">
                                    <i class="fas fa-arrow-left me-2"></i>Back to Translator
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="footer bg-dark text-light">
            <div class="container">
                <div class="row">
                    <div class="col-md-6">
                        <p><i class="fas fa-code me-2"></i>Command Translator</p>
                        <p class="small">Copyright &copy; 2024 Command Translator</p>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <p class="small watermark-label">Security Token: {watermark}</p>
                    </div>
                </div>
            </div>
        </footer>

        <!-- JavaScript Bundle with Popper -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

def get_linux_command(query):
    if not openai_client:
        return {
            "command": "ERROR: API key required",
            "explanation": "An OpenAI API key is required to translate to Linux commands."
        }
    
    try:
        system_prompt = """
        You are a Linux command translator. Convert natural language requests into appropriate Linux shell commands.
        Keep your responses concise. Provide:
        1. The exact Linux command to execute
        2. A brief explanation of what the command does and why it works
        
        Focus on common Linux utilities and ensure commands are safe to execute. 
        Avoid destructive operations like deleting or formatting without explicit confirmation.
        
        Respond with valid JSON in this format:
        {
            "command": "the_linux_command",
            "explanation": "Brief explanation of what the command does and how it works"
        }
        
        Copyright (c) 2024 Command Translator
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o", # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {
            "command": "ERROR",
            "explanation": f"Failed to process your request: {str(e)}"
        }

def get_powershell_command(query):
    if not openai_client:
        return {
            "command": "ERROR: API key required",
            "explanation": "An OpenAI API key is required to translate to PowerShell commands."
        }
    
    try:
        system_prompt = """
        You are a PowerShell command translator. Convert natural language requests into appropriate PowerShell commands.
        Keep your responses concise. Provide:
        1. The exact PowerShell command to execute
        2. A brief explanation of what the command does and why it works
        
        Focus on common PowerShell cmdlets and ensure commands are safe to execute. 
        Use modern PowerShell syntax and techniques when appropriate.
        Avoid destructive operations without explicit confirmation.
        
        Respond with valid JSON in this format:
        {
            "command": "the_powershell_command",
            "explanation": "Brief explanation of what the command does and how it works"
        }
        
        Copyright (c) 2024 Command Translator
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o", # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {
            "command": "ERROR",
            "explanation": f"Failed to process your request: {str(e)}"
        }

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
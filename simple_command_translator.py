import os
import subprocess
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up OpenAI API
import openai
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    logger.warning("No OpenAI API key found. Translation features will not work.")
else:
    openai.api_key = api_key

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Define safe Linux commands
SAFE_LINUX_COMMANDS = [
    'ls', 'pwd', 'cd', 'echo', 'cat', 'head', 'tail', 
    'grep', 'find', 'wc', 'date', 'cal', 'uname', 'whoami',
    'df', 'du', 'free', 'ps', 'uptime', 'w', 'finger',
    'id', 'groups', 'who', 'last', 'history',
    'chmod', 'chown', 'mkdir', 'rmdir', 'touch', 'mv', 'cp',
    'ln', 'less', 'more', 'sort', 'uniq', 'tr', 'cut', 'paste',
    'diff', 'file', 'tar', 'gzip', 'gunzip', 'zip', 'unzip',
    'hostname', 'ping', 'traceroute', 'ifconfig', 'netstat',
    'ss', 'dig', 'nslookup', 'host',
    # Additional common Linux commands
    'awk', 'sed', 'top', 'htop', 'curl', 'wget', 'jq',
    'journalctl', 'systemctl', 'lsblk', 'df', 'du',
    'find', 'xargs', 'rsync', 'scp', 'sftp',
    'ssh', 'sshd', 'passwd', 'mount', 'umount'
]

# Define safe PowerShell commands
SAFE_POWERSHELL_COMMANDS = [
    'Get-ChildItem', 'Get-Location', 'Set-Location', 'Write-Output',
    'Get-Content', 'Select-String', 'Get-Process', 'Get-Date',
    'Get-Service', 'Get-Command', 'Test-Path', 'Get-Item', 
    'Format-List', 'Format-Table', 'Measure-Object', 'Where-Object',
    'Select-Object', 'Sort-Object', 'Get-Member', 'Get-Help',
    'Get-PSDrive', 'Get-ItemProperty', 'Get-Alias', 'New-Item',
    'Copy-Item', 'Move-Item', 'Rename-Item', 'Remove-Item',
    'New-PSDrive', 'Get-Host', 'Get-History', 'Invoke-History',
    'Get-ComputerInfo', 'Get-NetIPAddress', 'Get-NetAdapter',
    'Get-Disk', 'Get-Volume', 'Get-Partition',
    # Additional PowerShell commands
    'Get-WmiObject', 'Invoke-Command', 'Start-Process', 'Stop-Process',
    'Get-EventLog', 'Write-Host', 'Out-File', 'Import-Csv', 'Export-Csv',
    'ConvertTo-Json', 'ConvertFrom-Json', 'Get-FileHash', 'Get-Random',
    'Get-Credential', 'New-TimeSpan', 'Measure-Command', 'Start-Job',
    'Receive-Job', 'Out-GridView', 'Clear-Host', 'Clear-Content',
    'Compare-Object', 'Get-Module', 'Import-Module', 'Remove-Module',
    'Get-ExecutionPolicy', 'Set-ExecutionPolicy', 'Test-Connection'
]

# Function to check if a Linux command is safe to execute
def is_safe_linux_command(command):
    """Check if a Linux command is safe to execute"""
    if not command:
        return False
    
    # Extract the base command (before any options)
    cmd_parts = command.strip().split()
    if not cmd_parts:
        return False
    
    main_cmd = cmd_parts[0]
    
    # Check if the command is in our safe list
    return main_cmd in SAFE_LINUX_COMMANDS

# Function to check if a PowerShell command is safe to execute
def is_safe_powershell_command(command):
    """Check if a PowerShell command is safe to execute"""
    if not command:
        return False
    
    # Extract the base command (before any options)
    cmd_parts = command.strip().split()
    if not cmd_parts:
        return False
    
    main_cmd = cmd_parts[0]
    
    # Check if the command is in our safe list
    return main_cmd in SAFE_POWERSHELL_COMMANDS

# Sanitize input
def sanitize_input(text):
    """Sanitize user input"""
    if not text:
        return ""
    
    # Limit length
    return text[:1000]

# Routes
@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/directory')
def directory():
    """Render the directory page with links to all interfaces"""
    return render_template('directory.html')

@app.route('/simple')
def simple():
    """Render the simple home page with both Linux and PowerShell options"""
    return render_template('simple.html')

@app.route('/form-linux')
def form_linux():
    """Render the form-based Linux translator"""
    return render_template('form_linux.html')

@app.route('/form-powershell')
def form_powershell():
    """Render the form-based PowerShell translator"""
    return render_template('form_powershell.html')

@app.route('/form-translate-linux', methods=['POST'])
def form_translate_linux():
    """Process Linux translation form"""
    query = request.form.get('query', '')
    
    if not query:
        return render_template('form_linux.html', error="Please provide a query.")
    
    # Get Linux command
    command = get_linux_command(query)
    
    return render_template('form_linux_result.html', query=query, command=command)

@app.route('/form-translate-powershell', methods=['POST'])
def form_translate_powershell():
    """Process PowerShell translation form"""
    query = request.form.get('query', '')
    
    if not query:
        return render_template('form_powershell.html', error="Please provide a query.")
    
    # Get PowerShell command
    command = get_powershell_command(query)
    
    return render_template('form_powershell_result.html', query=query, command=command)

# Sample user database (in-memory for simplicity)
USERS = {
    'admin': {
        'password_hash': generate_password_hash('admin123'),
        'email': 'admin@example.com'
    },
    'user': {
        'password_hash': generate_password_hash('user123'),
        'email': 'user@example.com'
    }
}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user exists and password is correct
        if username in USERS and check_password_hash(USERS[username]['password_hash'], password):
            session['user_id'] = username
            
            # Redirect to next parameter if provided, otherwise to index
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('index'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out the current user"""
    session.pop('user_id', None)
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        # Check if username already exists
        if username in USERS:
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        # Add new user
        USERS[username] = {
            'password_hash': generate_password_hash(password),
            'email': email
        }
        
        # Log in the new user
        session['user_id'] = username
        flash('Account created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    """Display user profile"""
    username = session.get('user_id')
    if not username or username not in USERS:
        return redirect(url_for('logout'))
        
    return render_template('profile.html', username=username, email=USERS[username]['email'])

@app.route('/execute', methods=['POST'])
def execute_command():
    """Execute a command in a real environment and return the results
    Enhanced to provide more context about the real Linux/PowerShell environment
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    command = request.form.get('command', '')
    mode = request.form.get('mode', 'linux')
    working_dir = request.form.get('workingDir', '.')
    
    # Log the command execution request
    logger.info(f"Command execution request: '{command}' (mode: {mode})")
    
    if not command:
        return jsonify({"error": "No command provided"}), 400
    
    # Record the username if logged in
    username = session.get('user_id', 'anonymous')
    
    output = ""
    error = ""
    execution_info = {}
    
    # Get system info for extra context
    try:
        import platform
        system_info = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        execution_info["system_info"] = system_info
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
    
    # Get current timestamp
    from datetime import datetime
    current_time = datetime.utcnow().isoformat() + "Z"
    
    if mode == 'linux':
        if is_safe_linux_command(command):
            try:
                # Get some environment info before execution
                env_result = subprocess.run(
                    "uname -a && whoami && pwd",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                execution_info["environment"] = env_result.stdout.strip()
                
                # Execute the command in a subprocess
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=10  # Increased timeout to 10 seconds
                )
                output = result.stdout
                error = result.stderr
                execution_info["exit_code"] = result.returncode
                
                # Log successful execution
                logger.info(f"Linux command executed successfully: '{command}' by user '{username}'")
            except subprocess.TimeoutExpired:
                error = "Command execution timed out after 10 seconds"
                logger.warning(f"Command execution timeout: '{command}' by user '{username}'")
            except Exception as e:
                error = f"Error executing command: {str(e)}"
                logger.error(f"Command execution error: '{command}' - {str(e)}")
        else:
            error = f"Command '{command}' is not in the allowed safe commands list"
            logger.warning(f"Unsafe command attempt: '{command}' by user '{username}'")
    elif mode == 'powershell':
        if is_safe_powershell_command(command):
            try:
                # Get some PowerShell environment info before execution
                env_command = "Write-Output 'PowerShell Info:'; $PSVersionTable; Write-Output 'User:'; whoami; Write-Output 'Location:'; Get-Location"
                env_result = subprocess.run(
                    ["powershell", "-Command", env_command],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                execution_info["environment"] = env_result.stdout.strip()
                
                # Execute the PowerShell command
                result = subprocess.run(
                    ["powershell", "-Command", command],
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=10  # Increased timeout to 10 seconds
                )
                output = result.stdout
                error = result.stderr
                execution_info["exit_code"] = result.returncode
                
                # Log successful execution
                logger.info(f"PowerShell command executed successfully: '{command}' by user '{username}'")
            except subprocess.TimeoutExpired:
                error = "Command execution timed out after 10 seconds"
                logger.warning(f"Command execution timeout: '{command}' by user '{username}'")
            except Exception as e:
                error = f"Error executing PowerShell command: {str(e)}"
                logger.error(f"PowerShell command execution error: '{command}' - {str(e)}")
        else:
            error = f"PowerShell command '{command}' is not in the allowed safe commands list"
            logger.warning(f"Unsafe PowerShell command attempt: '{command}' by user '{username}'")
    else:
        error = f"Unsupported mode: {mode}"
        logger.error(f"Unsupported mode: {mode} for command '{command}'")
    
    # Create a watermark for verification
    from hashlib import sha256
    execution_hash = sha256(f"{command}:{mode}:{username}:{current_time}".encode()).hexdigest()[:12]
    
    return jsonify({
        "output": output,
        "error": error,
        "working_directory": working_dir,
        "timestamp": current_time,
        "execution_info": execution_info,
        "execution_hash": execution_hash,
        "mode": mode,
        "command": command,
        "execution_user": username
    })

def get_linux_command(query):
    """
    Use OpenAI to translate natural language to Linux command
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    sanitized_query = sanitize_input(query)
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": "You are a Linux command expert. Generate only the exact command with no explanation or markdown formatting. The response should contain ONLY the command itself, nothing else."},
                {"role": "user", "content": f"Convert this request to a Linux command: {sanitized_query}"}
            ],
            temperature=0.2,
            max_tokens=150
        )
        
        command = response.choices[0].message.content.strip()
        logger.info(f"Linux command generated: {command}")
        
        return command
    except Exception as e:
        logger.error(f"Error generating Linux command: {str(e)}")
        return f"Error generating command. Please try again later. ({str(e)[:50]}...)"

def get_powershell_command(query):
    """
    Use OpenAI to translate natural language to PowerShell command
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    sanitized_query = sanitize_input(query)
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": "You are a PowerShell command expert. Generate only the exact PowerShell command with no explanation or markdown formatting. The response should contain ONLY the command itself, nothing else."},
                {"role": "user", "content": f"Convert this request to a PowerShell command: {sanitized_query}"}
            ],
            temperature=0.2,
            max_tokens=150
        )
        
        command = response.choices[0].message.content.strip()
        logger.info(f"PowerShell command generated: {command}")
        
        return command
    except Exception as e:
        logger.error(f"Error generating PowerShell command: {str(e)}")
        return f"Error generating PowerShell command. Please try again later. ({str(e)[:50]}...)"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
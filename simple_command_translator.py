import os
import subprocess
import logging
import socket
import paramiko  # SSH client for remote Linux connections
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Set up OpenAI API
import openai
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# Remote connection configuration
REMOTE_SERVERS = {
    'linux': {
        'enabled': False,
        'host': os.environ.get('LINUX_SERVER_HOST', ''),
        'port': int(os.environ.get('LINUX_SERVER_PORT', 22)),
        'username': os.environ.get('LINUX_SERVER_USER', ''),
        'password': os.environ.get('LINUX_SERVER_PASSWORD', ''),
        'key_file': os.environ.get('LINUX_SERVER_KEY_FILE', '')
    },
    'powershell': {
        'enabled': False,
        'host': os.environ.get('PS_SERVER_HOST', ''),
        'port': int(os.environ.get('PS_SERVER_PORT', 5985)),
        'username': os.environ.get('PS_SERVER_USER', ''),
        'password': os.environ.get('PS_SERVER_PASSWORD', ''),
        'use_ssl': os.environ.get('PS_SERVER_USE_SSL', 'False').lower() == 'true'
    }
}

# Update enabled status based on host configuration
REMOTE_SERVERS['linux']['enabled'] = bool(REMOTE_SERVERS['linux']['host'])
REMOTE_SERVERS['powershell']['enabled'] = bool(REMOTE_SERVERS['powershell']['host'])

def execute_remote_linux_command(command, working_dir='.'):
    """
    Execute a command on a remote Linux server via SSH
    Returns (output, error, exit_code)
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    if not REMOTE_SERVERS['linux']['enabled']:
        return '', 'Remote Linux execution is not configured', 1
    
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the remote server
        if REMOTE_SERVERS['linux']['key_file']:
            # Use key file authentication
            ssh.connect(
                REMOTE_SERVERS['linux']['host'],
                port=REMOTE_SERVERS['linux']['port'],
                username=REMOTE_SERVERS['linux']['username'],
                key_filename=REMOTE_SERVERS['linux']['key_file'],
                timeout=10
            )
        else:
            # Use password authentication
            ssh.connect(
                REMOTE_SERVERS['linux']['host'],
                port=REMOTE_SERVERS['linux']['port'],
                username=REMOTE_SERVERS['linux']['username'],
                password=REMOTE_SERVERS['linux']['password'],
                timeout=10
            )
        
        # Change to the specified working directory if provided
        if working_dir and working_dir != '.':
            cd_command = f'cd {working_dir} && '
        else:
            cd_command = ''
        
        # Execute the command
        full_command = cd_command + command
        stdin, stdout, stderr = ssh.exec_command(full_command, timeout=15)
        
        # Get the output and error
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_code = stdout.channel.recv_exit_status()
        
        # Close the connection
        ssh.close()
        
        return output, error, exit_code
    except Exception as e:
        logger.error(f"Error executing remote Linux command: {str(e)}")
        return '', f"Error connecting to remote Linux server: {str(e)}", 1

def execute_remote_powershell_command(command, working_dir='.'):
    """
    Execute a command on a remote Windows server via WinRM/PowerShell
    Returns (output, error, exit_code)
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    if not REMOTE_SERVERS['powershell']['enabled']:
        return '', 'Remote PowerShell execution is not configured', 1
    
    try:
        # For PowerShell remoting, we need to use different approaches
        # This is a simplified implementation for demonstration purposes
        # In a production environment, you would use pywinrm or similar libraries
        
        # Fallback to using SSH if available (for PowerShell Core on Linux)
        try:
            import winrm
            
            # Create WinRM session
            session = winrm.Session(
                REMOTE_SERVERS['powershell']['host'],
                auth=(REMOTE_SERVERS['powershell']['username'], REMOTE_SERVERS['powershell']['password']),
                transport='ssl' if REMOTE_SERVERS['powershell']['use_ssl'] else 'ntlm',
                server_cert_validation='ignore'
            )
            
            # Change to the specified working directory if provided
            if working_dir and working_dir != '.':
                cd_command = f'Set-Location -Path "{working_dir}"; '
            else:
                cd_command = ''
            
            # Execute the command
            full_command = cd_command + command
            result = session.run_ps(full_command)
            
            return result.std_out.decode('utf-8'), result.std_err.decode('utf-8'), result.status_code
        except ImportError:
            return '', 'WinRM Python package not installed. Please install winrm package.', 1
    except Exception as e:
        logger.error(f"Error executing remote PowerShell command: {str(e)}")
        return '', f"Error connecting to remote Windows server: {str(e)}", 1

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

@app.route('/remote-setup')
def remote_setup():
    """Render the remote server setup page"""
    # Check if user is logged in
    if session.get('user_id') is None:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login', next=request.url))
        
    return render_template('remote_setup.html', 
                           linux_config=REMOTE_SERVERS['linux'],
                           powershell_config=REMOTE_SERVERS['powershell'])

@app.route('/remote-setup/save', methods=['POST'])
def save_remote_setup():
    """Save remote server configuration"""
    # Check if user is logged in
    if session.get('user_id') is None:
        return jsonify({
            "success": False,
            "message": "Please log in to access this functionality"
        })
        
    server_type = request.form.get('server_type')
    test_only = request.form.get('test_only') == 'true'
    
    if server_type not in ['linux', 'powershell']:
        return jsonify({
            "success": False,
            "message": "Invalid server type"
        })
    
    # Only administrators can modify server configuration
    username = session.get('user_id', '')
    if username != 'admin':
        return jsonify({
            "success": False,
            "message": "Only administrators can modify server configuration"
        })
    
    # Get form data
    enabled = request.form.get('enabled') == 'on'
    host = request.form.get('host', '')
    port = request.form.get('port', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    # Update server configuration in memory
    REMOTE_SERVERS[server_type]['enabled'] = enabled and bool(host)
    REMOTE_SERVERS[server_type]['host'] = host
    REMOTE_SERVERS[server_type]['port'] = int(port) if port.isdigit() else (22 if server_type == 'linux' else 5985)
    REMOTE_SERVERS[server_type]['username'] = username
    
    # Only update password if provided
    if password:
        REMOTE_SERVERS[server_type]['password'] = password
    
    # Handle server-specific configuration
    if server_type == 'linux':
        auth_method = request.form.get('auth_method')
        if auth_method == 'key':
            key_file = request.form.get('key_file', '')
            REMOTE_SERVERS[server_type]['key_file'] = key_file
        else:
            REMOTE_SERVERS[server_type]['key_file'] = ''
    elif server_type == 'powershell':
        use_ssl = request.form.get('use_ssl') == 'true'
        REMOTE_SERVERS[server_type]['use_ssl'] = use_ssl
    
    # If this is just a test, don't save to environment variables
    if test_only:
        # Test the connection
        if server_type == 'linux':
            try:
                if not host or not username:
                    return jsonify({
                        "success": False,
                        "message": "Host and username are required"
                    })
                
                # Try to establish SSH connection
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if REMOTE_SERVERS['linux']['key_file']:
                    # Use key file authentication
                    ssh.connect(
                        host,
                        port=REMOTE_SERVERS['linux']['port'],
                        username=REMOTE_SERVERS['linux']['username'],
                        key_filename=REMOTE_SERVERS['linux']['key_file'],
                        timeout=5
                    )
                else:
                    # Use password authentication
                    ssh.connect(
                        host,
                        port=REMOTE_SERVERS['linux']['port'],
                        username=REMOTE_SERVERS['linux']['username'],
                        password=REMOTE_SERVERS['linux']['password'],
                        timeout=5
                    )
                
                # Execute a simple command to test
                stdin, stdout, stderr = ssh.exec_command("uname -a", timeout=3)
                output = stdout.read().decode('utf-8').strip()
                
                # Close the connection
                ssh.close()
                
                return jsonify({
                    "success": True,
                    "message": f"Successfully connected to Linux server: {output}"
                })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "message": f"Failed to connect to Linux server: {str(e)}"
                })
        else:  # PowerShell
            try:
                if not host or not username:
                    return jsonify({
                        "success": False,
                        "message": "Host and username are required"
                    })
                
                # First try a simple socket connection
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((host, REMOTE_SERVERS['powershell']['port']))
                s.close()
                
                # Try to use WinRM if available
                try:
                    import winrm
                    
                    # Create WinRM session
                    session = winrm.Session(
                        host,
                        auth=(REMOTE_SERVERS['powershell']['username'], REMOTE_SERVERS['powershell']['password']),
                        transport='ssl' if REMOTE_SERVERS['powershell']['use_ssl'] else 'ntlm',
                        server_cert_validation='ignore'
                    )
                    
                    # Try to execute a simple command
                    result = session.run_ps("$PSVersionTable.PSVersion.ToString()")
                    
                    if result.status_code == 0:
                        return jsonify({
                            "success": True,
                            "message": f"Successfully connected to Windows server: PowerShell {result.std_out.decode('utf-8').strip()}"
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "message": f"Connected to server but PowerShell command failed: {result.std_err.decode('utf-8')}"
                        })
                except ImportError:
                    return jsonify({
                        "success": True,
                        "message": "Connected to Windows server (basic connection only, WinRM package not available)"
                    })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "message": f"Failed to connect to Windows server: {str(e)}"
                })
    else:
        # TODO: In a production environment, we would save these to environment variables
        # or a secure configuration store, but for this demo we'll just keep them in memory
        
        flash(f"{server_type.capitalize()} server configuration updated", 'success')
        return redirect(url_for('remote_setup'))
    
    # This should never be reached
    return jsonify({
        "success": False,
        "message": "Unknown error"
    })

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

@app.route('/api/connection-status')
def connection_status():
    """Get the status of remote system connections"""
    linux_status = "Not configured"
    powershell_status = "Not configured"
    
    # Check Linux connection
    if REMOTE_SERVERS['linux']['enabled']:
        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try to connect with a short timeout
            if REMOTE_SERVERS['linux']['key_file']:
                ssh.connect(
                    REMOTE_SERVERS['linux']['host'],
                    port=REMOTE_SERVERS['linux']['port'],
                    username=REMOTE_SERVERS['linux']['username'],
                    key_filename=REMOTE_SERVERS['linux']['key_file'],
                    timeout=3
                )
            else:
                ssh.connect(
                    REMOTE_SERVERS['linux']['host'],
                    port=REMOTE_SERVERS['linux']['port'],
                    username=REMOTE_SERVERS['linux']['username'],
                    password=REMOTE_SERVERS['linux']['password'],
                    timeout=3
                )
            
            # If we reach here, the connection was successful
            linux_status = "Connected"
            
            # Get system info
            stdin, stdout, stderr = ssh.exec_command("uname -a", timeout=2)
            system_info = stdout.read().decode('utf-8').strip()
            if system_info:
                linux_status = f"Connected: {system_info}"
            
            # Close the connection
            ssh.close()
        except Exception as e:
            linux_status = f"Error: {str(e)}"
            logger.error(f"Error checking Linux connection: {str(e)}")
    
    # Check PowerShell connection
    if REMOTE_SERVERS['powershell']['enabled']:
        try:
            # For PowerShell, we'll try a simple socket connection first
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((REMOTE_SERVERS['powershell']['host'], REMOTE_SERVERS['powershell']['port']))
            s.close()
            
            # If we reach here, we can at least reach the server
            powershell_status = "Connected"
            
            # Try to use WinRM if available
            try:
                import winrm
                
                # Create WinRM session
                session = winrm.Session(
                    REMOTE_SERVERS['powershell']['host'],
                    auth=(REMOTE_SERVERS['powershell']['username'], REMOTE_SERVERS['powershell']['password']),
                    transport='ssl' if REMOTE_SERVERS['powershell']['use_ssl'] else 'ntlm',
                    server_cert_validation='ignore'
                )
                
                # Try to get system info
                result = session.run_ps("$PSVersionTable | ConvertTo-Json")
                if result.status_code == 0:
                    powershell_status = f"Connected: PowerShell {result.std_out.decode('utf-8')[:30]}..."
            except Exception as e:
                # Just use the socket connection status, don't report this error
                pass
        except Exception as e:
            powershell_status = f"Error: {str(e)}"
            logger.error(f"Error checking PowerShell connection: {str(e)}")
    
    return jsonify({
        "linux": {
            "enabled": REMOTE_SERVERS['linux']['enabled'],
            "status": linux_status,
            "host": REMOTE_SERVERS['linux']['host'] if REMOTE_SERVERS['linux']['enabled'] else None
        },
        "powershell": {
            "enabled": REMOTE_SERVERS['powershell']['enabled'],
            "status": powershell_status,
            "host": REMOTE_SERVERS['powershell']['host'] if REMOTE_SERVERS['powershell']['enabled'] else None
        }
    })

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
    Support for direct connection to remote PowerShell and Linux systems
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
    
    # Check if remote execution is requested
    remote_execution = request.form.get('remote', 'false').lower() == 'true'
    connection_info = {}
    
    # Initialize remote session vars
    remote_session = None
    remote_session_id = None
    
    # Create a DNA-based watermark for the session
    from utils import create_dna_signature
    from hashlib import sha256
    
    # Import the models
    from models import db, RemoteSession, CommandHistory
    
    # Create session hash for tracking
    session_hash = sha256(f"{username}:{mode}:{datetime.utcnow().isoformat()}".encode()).hexdigest()
    dna_watermark = create_dna_signature(f"session:{username}:{mode}:{datetime.utcnow().isoformat()}")
    client_ip = request.remote_addr
    
    if mode == 'linux':
        if is_safe_linux_command(command):
            try:
                if remote_execution and REMOTE_SERVERS['linux']['enabled']:
                    # Get remote execution info
                    connection_info = {
                        "host": REMOTE_SERVERS['linux']['host'],
                        "port": REMOTE_SERVERS['linux']['port'],
                        "username": REMOTE_SERVERS['linux']['username'],
                        "using_key": bool(REMOTE_SERVERS['linux']['key_file']),
                    }
                    execution_info["connection"] = connection_info
                    
                    # Create a remote session record in the database
                    user_id = None
                    if 'user_id' in session:
                        user_id = session.get('user_id')
                    
                    # Create a new remote session in the database
                    remote_session = RemoteSession(
                        user_id=user_id,
                        session_type='linux',
                        host=REMOTE_SERVERS['linux']['host'],
                        port=REMOTE_SERVERS['linux']['port'],
                        username=REMOTE_SERVERS['linux']['username'],
                        ip_address=client_ip,
                        session_hash=session_hash,
                        session_watermark=dna_watermark
                    )
                    db.session.add(remote_session)
                    db.session.commit()
                    remote_session_id = remote_session.id
                    
                    # Use remote Linux execution
                    logger.info(f"Executing command on remote Linux server: {REMOTE_SERVERS['linux']['host']}")
                    remote_output, remote_error, exit_code = execute_remote_linux_command(command, working_dir)
                    output = remote_output
                    error = remote_error
                    execution_info["exit_code"] = exit_code
                    execution_info["executed_on"] = "remote-linux"
                    
                    # Add environment info if available
                    if not error:
                        # Try to get environment info from remote system
                        env_output, env_error, _ = execute_remote_linux_command("uname -a && whoami && pwd", working_dir)
                        if not env_error:
                            execution_info["environment"] = env_output.strip()
                else:
                    # Get some environment info before execution (local)
                    env_result = subprocess.run(
                        "uname -a && whoami && pwd",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    execution_info["environment"] = env_result.stdout.strip()
                    execution_info["executed_on"] = "local"
                    
                    # Execute the command in a subprocess (local)
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
                if remote_execution and REMOTE_SERVERS['powershell']['enabled']:
                    # Get remote execution info
                    connection_info = {
                        "host": REMOTE_SERVERS['powershell']['host'],
                        "port": REMOTE_SERVERS['powershell']['port'],
                        "username": REMOTE_SERVERS['powershell']['username'],
                        "using_ssl": REMOTE_SERVERS['powershell']['use_ssl'],
                    }
                    execution_info["connection"] = connection_info
                    
                    # Create a remote session record in the database
                    user_id = None
                    if 'user_id' in session:
                        user_id = session.get('user_id')
                    
                    # Create a new remote session in the database
                    remote_session = RemoteSession(
                        user_id=user_id,
                        session_type='powershell',
                        host=REMOTE_SERVERS['powershell']['host'],
                        port=REMOTE_SERVERS['powershell']['port'],
                        username=REMOTE_SERVERS['powershell']['username'],
                        ip_address=client_ip,
                        session_hash=session_hash,
                        session_watermark=dna_watermark
                    )
                    db.session.add(remote_session)
                    db.session.commit()
                    remote_session_id = remote_session.id
                    
                    # Use remote PowerShell execution
                    logger.info(f"Executing command on remote Windows server: {REMOTE_SERVERS['powershell']['host']}")
                    remote_output, remote_error, exit_code = execute_remote_powershell_command(command, working_dir)
                    output = remote_output
                    error = remote_error
                    execution_info["exit_code"] = exit_code
                    execution_info["executed_on"] = "remote-powershell"
                    
                    # Add environment info if available
                    if not error:
                        # Try to get environment info from remote system
                        env_command = "Write-Output 'PowerShell Info:'; $PSVersionTable; Write-Output 'User:'; whoami; Write-Output 'Location:'; Get-Location"
                        env_output, env_error, _ = execute_remote_powershell_command(env_command, working_dir)
                        if not env_error:
                            execution_info["environment"] = env_output.strip()
                else:
                    # Get some PowerShell environment info before execution (local)
                    env_command = "Write-Output 'PowerShell Info:'; $PSVersionTable; Write-Output 'User:'; whoami; Write-Output 'Location:'; Get-Location"
                    env_result = subprocess.run(
                        ["powershell", "-Command", env_command],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    execution_info["environment"] = env_result.stdout.strip()
                    execution_info["executed_on"] = "local"
                    
                    # Execute the PowerShell command (local)
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
    
    # Create a watermark for verification using Ervin's DNA-based security technology
    from hashlib import sha256
    from utils import create_dna_signature
    
    # Base hash with command details
    base_hash = sha256(f"{command}:{mode}:{username}:{current_time}".encode()).hexdigest()[:12]
    
    # Enhanced DNA-based watermark for security tracing
    execution_environment = "remote" if remote_execution else "local"
    dna_marker = create_dna_signature(f"{command}:{mode}:{username}:{execution_environment}:{current_time}")
    
    # Final execution hash combines both for traceability
    execution_hash = f"{base_hash}:{dna_marker[:8]}"
    
    # Record command in history if logged in
    user_id = None
    if 'user_id' in session:
        user_id = session.get('user_id')
        
    # Create command history entry in database
    try:
        history_entry = CommandHistory(
            user_id=user_id,
            query=request.form.get('query', 'Direct execution'),
            command=command,
            command_type=mode,
            executed=True,
            execution_output=output if not error else error,
            execution_success=(not error),
            ip_address=client_ip,
            remote_execution=remote_execution,
            command_hash=base_hash,
            watermark=dna_marker,
            remote_session_id=remote_session_id
        )
        db.session.add(history_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error recording command history: {str(e)}")
    
    # Close remote session if applicable
    if remote_execution and remote_session_id:
        try:
            # Update the remote session with end time
            remote_session = RemoteSession.query.get(remote_session_id)
            if remote_session:
                remote_session.end_time = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            logger.error(f"Error closing remote session: {str(e)}")
    
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

@app.route('/remote-sessions')
@login_required
def remote_sessions():
    """Display and filter remote sessions"""
    from models import RemoteSession
    
    # Get filters from query parameters
    session_type = request.args.get('session_type', '')
    host = request.args.get('host', '')
    date = request.args.get('date', '')
    
    # Build base query
    query = RemoteSession.query
    
    # Apply filters
    if session_type:
        query = query.filter(RemoteSession.session_type == session_type)
    if host:
        query = query.filter(RemoteSession.host.like(f'%{host}%'))
    if date:
        import datetime
        filter_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        next_day = filter_date + datetime.timedelta(days=1)
        query = query.filter(RemoteSession.start_time >= filter_date, 
                             RemoteSession.start_time < next_day)
    
    # Get the user's sessions only
    user_id = session.get('user_id')
    query = query.filter(RemoteSession.user_id == user_id)
    
    # Order by most recent first
    query = query.order_by(RemoteSession.start_time.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    sessions = pagination.items
    
    return render_template('remote_sessions.html', sessions=sessions, pagination=pagination, request=request)


@app.route('/remote-session-details/<int:session_id>')
@login_required
def remote_session_details(session_id):
    """Display details of a specific remote session"""
    from models import RemoteSession, CommandHistory
    
    # Get the session
    remote_session = RemoteSession.query.get_or_404(session_id)
    
    # Security check: ensure the user owns this session
    if remote_session.user_id != session.get('user_id'):
        flash('You do not have permission to view this session.', 'danger')
        return redirect(url_for('remote_sessions'))
    
    # Get commands for this session
    commands = CommandHistory.query.filter_by(remote_session_id=session_id).order_by(CommandHistory.created_at).all()
    
    return render_template('remote_session_details.html', session=remote_session, commands=commands)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
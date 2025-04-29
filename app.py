import os
import json
import time
import uuid
import hashlib
import subprocess
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import openai

from models import db, User, CommandHistory, Favorite, CustomCommand, SecurityAudit, CommandLibrary, LibraryCommand, License
from utils import validate_linux_command, generate_command_hash, sanitize_input, log_command_request

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Set OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

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
    'ss', 'dig', 'nslookup', 'host'
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
    'Get-Disk', 'Get-Volume', 'Get-Partition'
]

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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

# Routes
@app.route('/')
def index():
    """
    Render the home page with links to various translator options
    """
    return render_template('index.html')

@app.route('/directory')
def directory():
    """
    Render the directory page with links to all interfaces
    """
    return render_template('directory.html')

@app.route('/standalone-powershell')
def standalone_powershell():
    """
    Render the standalone PowerShell translator with minimal dependencies
    """
    return render_template('standalone_powershell.html')

@app.route('/micro-powershell')
def micro_powershell():
    """
    Render the micro PowerShell translator with extremely simplified JavaScript
    """
    return render_template('micro_powershell.html')

@app.route('/form-powershell')
def form_powershell():
    """
    Render the form-based PowerShell translator without any JavaScript
    """
    return render_template('form_powershell.html')

@app.route('/form-linux')
def form_linux():
    """
    Render the form-based Linux translator without any JavaScript
    """
    return render_template('form_linux.html')

@app.route('/simple')
def simple():
    """
    Render the simple home page with both Linux and PowerShell options
    """
    return render_template('simple.html')

@app.route('/direct-translate', methods=['POST'])
def direct_translate():
    """
    Process translation form submission from the direct interface
    """
    query = request.form.get('query', '')
    mode = request.form.get('mode', 'linux')
    
    if not query:
        return "Please provide a query."
    
    # Process the query based on the mode
    if mode == 'linux':
        command = get_linux_command(query)
    else:
        command = get_powershell_command(query)
    
    # Store in command history with current session ID
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    # Get user ID if logged in
    user_id = session.get('user_id')
    
    # Store in database
    command_hash = generate_command_hash(command)
    watermark = generate_watermark(command, str(datetime.utcnow()))
    
    # Check risk level using utils function (simplified here)
    if mode == 'linux':
        is_safe, reason, risk_level = validate_linux_command(command)
    else:
        risk_level = 0  # Simplified for now
    
    # Store in database
    cmd_history = CommandHistory(
        user_id=user_id,
        query=query,
        command=command,
        command_type=mode,
        ip_address=request.remote_addr,
        command_hash=command_hash,
        watermark=watermark,
        risk_level=risk_level
    )
    
    db.session.add(cmd_history)
    db.session.commit()
    
    return f"Query: {query}<br>Command: {command}"

@app.route('/direct')
def direct():
    """
    Render the direct ultra-simple interface with no templates
    """
    return """
    <html>
    <head>
        <title>Command Translator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            form { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; }
            input[type="text"] { width: 300px; padding: 5px; }
            input[type="submit"] { padding: 5px 10px; background: #4CAF50; color: white; border: none; cursor: pointer; }
            .option { margin-right: 10px; }
        </style>
    </head>
    <body>
        <h1>Command Translator</h1>
        <form action="/direct-translate" method="post">
            <label for="query">Enter your query:</label>
            <input type="text" id="query" name="query" required>
            <div style="margin: 10px 0;">
                <span class="option"><input type="radio" id="linux" name="mode" value="linux" checked> <label for="linux">Linux</label></span>
                <span class="option"><input type="radio" id="powershell" name="mode" value="powershell"> <label for="powershell">PowerShell</label></span>
            </div>
            <input type="submit" value="Translate">
        </form>
        <div>
            <a href="/">Return to Home</a>
        </div>
    </body>
    </html>
    """

@app.route('/simple-translate', methods=['POST'])
def simple_translate():
    """
    Process translation form submission from the simple interface
    """
    query = request.form.get('query', '')
    mode = request.form.get('mode', 'linux')
    
    if not query:
        return render_template('simple.html', error="Please provide a query.")
    
    # Process the query based on the mode
    if mode == 'linux':
        command = get_linux_command(query)
    else:
        command = get_powershell_command(query)
    
    # Store in command history with current session ID
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    # Get user ID if logged in
    user_id = session.get('user_id')
    
    # Store in database
    command_hash = generate_command_hash(command)
    watermark = generate_watermark(command, str(datetime.utcnow()))
    
    # Check risk level using utils function (simplified here)
    if mode == 'linux':
        is_safe, reason, risk_level = validate_linux_command(command)
    else:
        risk_level = 0  # Simplified for now
    
    # Store in database
    cmd_history = CommandHistory(
        user_id=user_id,
        query=query,
        command=command,
        command_type=mode,
        ip_address=request.remote_addr,
        command_hash=command_hash,
        watermark=watermark,
        risk_level=risk_level
    )
    
    db.session.add(cmd_history)
    db.session.commit()
    
    return render_template('simple_result.html', query=query, command=command, mode=mode)

@app.route('/form-translate-powershell', methods=['POST'])
def form_translate_powershell():
    """
    Process PowerShell translation form and render results
    """
    query = request.form.get('query', '')
    
    if not query:
        return render_template('form_powershell.html', error="Please provide a query.")
    
    # Get PowerShell command
    command = get_powershell_command(query)
    
    # Store in command history
    user_id = session.get('user_id')
    
    # Store in database
    command_hash = generate_command_hash(command)
    watermark = generate_watermark(command, str(datetime.utcnow()))
    
    # Store in database
    cmd_history = CommandHistory(
        user_id=user_id,
        query=query,
        command=command,
        command_type='powershell',
        ip_address=request.remote_addr,
        command_hash=command_hash,
        watermark=watermark,
        risk_level=0
    )
    
    db.session.add(cmd_history)
    db.session.commit()
    
    return render_template('form_powershell_result.html', query=query, command=command)

@app.route('/form-translate-linux', methods=['POST'])
def form_translate_linux():
    """
    Process Linux translation form and render results
    """
    query = request.form.get('query', '')
    
    if not query:
        return render_template('form_linux.html', error="Please provide a query.")
    
    # Get Linux command
    command = get_linux_command(query)
    
    # Store in command history
    user_id = session.get('user_id')
    
    # Store in database
    command_hash = generate_command_hash(command)
    watermark = generate_watermark(command, str(datetime.utcnow()))
    
    # Check risk level
    is_safe, reason, risk_level = validate_linux_command(command)
    
    # Store in database
    cmd_history = CommandHistory(
        user_id=user_id,
        query=query,
        command=command,
        command_type='linux',
        ip_address=request.remote_addr,
        command_hash=command_hash,
        watermark=watermark,
        risk_level=risk_level
    )
    
    db.session.add(cmd_history)
    db.session.commit()
    
    return render_template('form_linux_result.html', query=query, command=command)

@app.route('/powershell')
def powershell():
    """
    Render the PowerShell command translator interface
    Copyright (c) 2024
    """
    return render_template('powershell.html')

@app.route('/powershell-link')
def powershell_link():
    """
    Render a direct link to the PowerShell interface
    """
    return redirect(url_for('powershell'))

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
    """
    API endpoint to translate natural language to a Linux command
    """
    data = request.get_json() if request.is_json else request.form
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    command = get_linux_command(query)
    
    # Store in command history
    user_id = session.get('user_id')
    command_hash = generate_command_hash(command)
    watermark = generate_watermark(command, str(datetime.utcnow()))
    is_safe, reason, risk_level = validate_linux_command(command)
    
    cmd_history = CommandHistory(
        user_id=user_id,
        query=query,
        command=command,
        command_type='linux',
        ip_address=request.remote_addr,
        command_hash=command_hash,
        watermark=watermark,
        risk_level=risk_level
    )
    
    db.session.add(cmd_history)
    db.session.commit()
    
    return jsonify({
        "command": command,
        "explanation": "This command will accomplish your requested task. Review carefully before execution.",
        "timestamp": datetime.utcnow().isoformat(),
        "watermark": watermark
    })

@app.route('/translate-powershell', methods=['POST'])
def translate_powershell():
    """
    Translate natural language to PowerShell command
    Copyright (c) 2024
    """
    data = request.get_json() if request.is_json else request.form
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    command = get_powershell_command(query)
    
    # Store in command history
    user_id = session.get('user_id')
    command_hash = generate_command_hash(command)
    watermark = generate_watermark(command, str(datetime.utcnow()))
    
    cmd_history = CommandHistory(
        user_id=user_id,
        query=query,
        command=command,
        command_type='powershell',
        ip_address=request.remote_addr,
        command_hash=command_hash,
        watermark=watermark,
        risk_level=0
    )
    
    db.session.add(cmd_history)
    db.session.commit()
    
    return jsonify({
        "command": command,
        "explanation": "This PowerShell command will accomplish your requested task. Review carefully before execution.",
        "timestamp": datetime.utcnow().isoformat(),
        "watermark": watermark
    })

@app.route('/execute', methods=['POST'])
def execute_command():
    """
    Execute a Linux command in a real environment and return the results
    Enhanced to provide more context about the real Linux environment
    """
    data = request.get_json() if request.is_json else request.form
    command = data.get('command', '')
    mode = data.get('mode', 'linux')
    working_dir = data.get('workingDir', '.')
    
    if not command:
        return jsonify({"error": "No command provided"}), 400
    
    output = ""
    error = ""
    
    if mode == 'linux':
        if is_safe_linux_command(command):
            try:
                # Execute the command in a subprocess
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stdout
                error = result.stderr
            except subprocess.TimeoutExpired:
                error = "Command execution timed out after 5 seconds"
            except Exception as e:
                error = f"Error executing command: {str(e)}"
        else:
            error = f"Command '{command}' is not in the allowed safe commands list"
    elif mode == 'powershell':
        if is_safe_powershell_command(command):
            try:
                # Execute the PowerShell command
                result = subprocess.run(
                    ["powershell", "-Command", command],
                    cwd=working_dir,
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
            error = f"PowerShell command '{command}' is not in the allowed safe commands list"
    else:
        error = f"Unsupported mode: {mode}"
    
    # Get user ID if logged in
    user_id = session.get('user_id')
    
    # Get command history entry if exists
    cmd_history = CommandHistory.query.filter_by(
        command=command, 
        command_type=mode,
        user_id=user_id
    ).order_by(CommandHistory.created_at.desc()).first()
    
    # If not found, create new entry
    if not cmd_history:
        cmd_history = CommandHistory(
            user_id=user_id,
            query="Direct execution",
            command=command,
            command_type=mode,
            ip_address=request.remote_addr
        )
        db.session.add(cmd_history)
    
    # Update with execution results
    cmd_history.executed = True
    cmd_history.execution_output = output if output else error
    cmd_history.execution_success = not error
    
    db.session.commit()
    
    return jsonify({
        "output": output,
        "error": error,
        "working_directory": working_dir,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required')
            return render_template('register.html')
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the new user
        session['user_id'] = new_user.id
        flash('Account created successfully!')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            
            # Redirect to next parameter if provided, otherwise to index
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out the current user"""
    session.pop('user_id', None)
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """Display user profile and command history"""
    user = User.query.get(session['user_id'])
    
    # Get user's command history
    history = CommandHistory.query.filter_by(user_id=user.id).order_by(CommandHistory.created_at.desc()).limit(50).all()
    
    # Get user's favorites
    favorites = Favorite.query.filter_by(user_id=user.id).all()
    
    return render_template(
        'profile.html', 
        user=user, 
        history=history, 
        favorites=favorites
    )

@app.route('/add-favorite', methods=['POST'])
@login_required
def add_favorite():
    """Add a command to favorites"""
    command = request.form.get('command')
    description = request.form.get('description')
    command_type = request.form.get('command_type', 'linux')
    
    if not command:
        flash('Command is required')
        return redirect(url_for('profile'))
    
    # Create new favorite
    new_favorite = Favorite(
        user_id=session['user_id'],
        command=command,
        description=description,
        command_type=command_type
    )
    
    db.session.add(new_favorite)
    db.session.commit()
    
    flash('Command added to favorites')
    return redirect(url_for('profile'))

@app.route('/remove-favorite/<int:favorite_id>', methods=['POST'])
@login_required
def remove_favorite(favorite_id):
    """Remove a command from favorites"""
    favorite = Favorite.query.get_or_404(favorite_id)
    
    # Check if favorite belongs to current user
    if favorite.user_id != session['user_id']:
        flash('You do not have permission to remove this favorite')
        return redirect(url_for('profile'))
    
    db.session.delete(favorite)
    db.session.commit()
    
    flash('Favorite removed')
    return redirect(url_for('profile'))

@app.route('/custom-commands')
@login_required
def custom_commands():
    """Display and manage custom commands"""
    user = User.query.get(session['user_id'])
    
    # Get user's custom commands
    commands = CustomCommand.query.filter_by(user_id=user.id).all()
    
    # Get public custom commands from other users
    public_commands = CustomCommand.query.filter(
        CustomCommand.is_public == True,
        CustomCommand.user_id != user.id
    ).all()
    
    return render_template(
        'custom_commands.html', 
        user=user, 
        commands=commands, 
        public_commands=public_commands
    )

@app.route('/add-custom-command', methods=['POST'])
@login_required
def add_custom_command():
    """Add a custom command template"""
    name = request.form.get('name')
    command_template = request.form.get('command_template')
    description = request.form.get('description')
    command_type = request.form.get('command_type', 'linux')
    is_public = 'is_public' in request.form
    
    if not name or not command_template:
        flash('Name and command template are required')
        return redirect(url_for('custom_commands'))
    
    # Create new custom command
    new_custom_command = CustomCommand(
        user_id=session['user_id'],
        name=name,
        command_template=command_template,
        description=description,
        command_type=command_type,
        is_public=is_public
    )
    
    db.session.add(new_custom_command)
    db.session.commit()
    
    flash('Custom command added')
    return redirect(url_for('custom_commands'))

@app.route('/edit-custom-command/<int:command_id>', methods=['POST'])
@login_required
def edit_custom_command(command_id):
    """Edit a custom command template"""
    custom_command = CustomCommand.query.get_or_404(command_id)
    
    # Check if command belongs to current user
    if custom_command.user_id != session['user_id']:
        flash('You do not have permission to edit this command')
        return redirect(url_for('custom_commands'))
    
    custom_command.name = request.form.get('name')
    custom_command.command_template = request.form.get('command_template')
    custom_command.description = request.form.get('description')
    custom_command.command_type = request.form.get('command_type', 'linux')
    custom_command.is_public = 'is_public' in request.form
    
    db.session.commit()
    
    flash('Custom command updated')
    return redirect(url_for('custom_commands'))

@app.route('/delete-custom-command/<int:command_id>', methods=['POST'])
@login_required
def delete_custom_command(command_id):
    """Delete a custom command template"""
    custom_command = CustomCommand.query.get_or_404(command_id)
    
    # Check if command belongs to current user
    if custom_command.user_id != session['user_id']:
        flash('You do not have permission to delete this command')
        return redirect(url_for('custom_commands'))
    
    db.session.delete(custom_command)
    db.session.commit()
    
    flash('Custom command deleted')
    return redirect(url_for('custom_commands'))

@app.route('/history')
@login_required
def history():
    """View command history with filtering options"""
    user = User.query.get(session['user_id'])
    
    # Get query parameters for filtering
    command_type = request.args.get('command_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    executed = request.args.get('executed')
    success = request.args.get('success')
    
    # Base query
    query = CommandHistory.query.filter_by(user_id=user.id)
    
    # Apply filters
    if command_type:
        query = query.filter_by(command_type=command_type)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(CommandHistory.created_at >= date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            date_to = date_to + timedelta(days=1)  # Include the end date
            query = query.filter(CommandHistory.created_at < date_to)
        except ValueError:
            pass
    
    if executed:
        query = query.filter_by(executed=(executed == 'yes'))
    
    if success:
        query = query.filter_by(execution_success=(success == 'yes'))
    
    # Order by created_at descending
    history = query.order_by(CommandHistory.created_at.desc()).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=20,
        error_out=False
    )
    
    return render_template(
        'history.html', 
        user=user, 
        history=history,
        filters={
            'command_type': command_type,
            'date_from': date_from,
            'date_to': date_to,
            'executed': executed,
            'success': success
        }
    )

@app.route('/api/command-libraries')
def api_command_libraries():
    """API endpoint to get command libraries"""
    libraries = CommandLibrary.query.all()
    
    result = []
    for library in libraries:
        lib_data = {
            'id': library.id,
            'name': library.name,
            'description': library.description,
            'command_type': library.command_type,
            'category': library.category,
            'commands': []
        }
        
        for cmd in library.commands:
            lib_data['commands'].append({
                'id': cmd.id,
                'command': cmd.command,
                'description': cmd.description,
                'example_usage': cmd.example_usage
            })
        
        result.append(lib_data)
    
    return jsonify(result)

# Helper Functions
def get_linux_command(query):
    """
    Use OpenAI to translate natural language to Linux command with improved formatting
    Copyright (c) 2024
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
        
        # Log the request
        log_command_request(sanitized_query, command, request.remote_addr, 'linux')
        
        return command
    except Exception as e:
        # Return a simple error message for the user
        return f"Error generating command. Please try again later. ({str(e)[:50]}...)"

def get_powershell_command(query):
    """
    Use OpenAI to translate natural language to PowerShell command
    Copyright (c) 2024
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
        
        # Log the request
        log_command_request(sanitized_query, command, request.remote_addr, 'powershell')
        
        return command
    except Exception as e:
        # Return a simple error message for the user
        return f"Error generating PowerShell command. Please try again later. ({str(e)[:50]}...)"

def generate_watermark(content, timestamp):
    """
    Generate a unique watermark based on content and timestamp
    - This is a simplified "DNA-based" security concept
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    # Create a hash of the content and timestamp
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    timestamp_hash = hashlib.sha256(timestamp.encode()).hexdigest()
    
    # Combine the hashes in an alternating pattern
    combined = ''
    for i in range(16):  # Taking first 16 characters from each hash
        combined += content_hash[i] + timestamp_hash[i]
    
    # Create the final watermark
    watermark = hashlib.sha256(combined.encode()).hexdigest()[:32]
    return watermark

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
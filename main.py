import os
import json
import subprocess
import shlex
from flask import Flask, request

# Create a simple Flask app
app = Flask(__name__)

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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Command Translator</title>
        <style>
            body { background-color: #333; color: white; font-family: Arial; padding: 20px; }
            form { background-color: #444; padding: 20px; max-width: 500px; margin: 0 auto; border-radius: 5px; }
            textarea { width: 100%; height: 100px; background-color: #222; color: white; margin: 10px 0; padding: 10px; }
            .result { background-color: #222; padding: 10px; margin-top: 10px; }
            .button-group { margin-top: 15px; display: flex; gap: 10px; }
            button { padding: 10px; border: none; border-radius: 3px; cursor: pointer; }
            .btn-translate { background-color: #4CAF50; color: white; }
            .btn-execute { background-color: #2196F3; color: white; }
            h1 { text-align: center; color: #4CAF50; }
            .mode-group { margin: 15px 0; }
        </style>
    </head>
    <body>
        <form action="/translate" method="post">
            <h1>Command Translator</h1>
            <textarea name="query" placeholder="Example: list all files sorted by size"></textarea>
            
            <div class="mode-group">
                <input type="radio" name="mode" value="linux" id="linux" checked>
                <label for="linux">Linux</label>
                <input type="radio" name="mode" value="powershell" id="powershell">
                <label for="powershell">PowerShell</label>
            </div>
            
            <div class="button-group">
                <button type="submit" class="btn-translate">Translate</button>
                <button type="submit" formaction="/execute" class="btn-execute">Translate & Execute</button>
            </div>
        </form>
    </body>
    </html>
    """

@app.route('/translate', methods=['POST'])
def translate():
    query = request.form.get('query', '')
    mode = request.form.get('mode', 'linux')
    
    if not query:
        return "Error: No query provided"
    
    if mode == 'powershell':
        result = get_powershell_command(query)
    else:
        result = get_linux_command(query)
    
    command = result.get('command', 'Error generating command')
    explanation = result.get('explanation', '')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Translation Result</title>
        <style>
            body {{ background-color: #333; color: white; font-family: Arial; padding: 20px; }}
            .container {{ background-color: #444; padding: 20px; max-width: 500px; margin: 0 auto; border-radius: 5px; }}
            .command {{ background-color: #222; color: #4CAF50; padding: 10px; margin: 10px 0; font-family: monospace; }}
            .explanation {{ background-color: #222; padding: 10px; margin: 10px 0; }}
            button {{ padding: 10px; border: none; border-radius: 3px; cursor: pointer; margin-top: 10px; }}
            .btn-execute {{ background-color: #2196F3; color: white; }}
            .back-link {{ display: block; text-align: center; margin-top: 20px; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Translation Result</h1>
            <h2>Command:</h2>
            <div class="command">{command}</div>
            <h2>Explanation:</h2>
            <div class="explanation">{explanation}</div>
            
            <form action="/execute" method="post">
                <input type="hidden" name="command" value="{command}">
                <input type="hidden" name="mode" value="{mode}">
                <button type="submit" class="btn-execute">Execute Command</button>
            </form>
            
            <a href="/" class="back-link">Back to Translator</a>
        </div>
    </body>
    </html>
    """

@app.route('/execute', methods=['POST'])
def execute():
    # Get command from form or translate a new query
    command = request.form.get('command', '')
    mode = request.form.get('mode', 'linux')
    query = request.form.get('query', '')
    
    # If no command but a query, translate it first
    if not command and query:
        if mode == 'powershell':
            result = get_powershell_command(query)
        else:
            result = get_linux_command(query)
        command = result.get('command', '')
        explanation = result.get('explanation', '')
    else:
        explanation = "Command execution"
    
    # Execute the command based on mode
    output = ""
    error = ""
    if command:
        if mode == 'powershell':
            # Simulate PowerShell execution
            output = f"PowerShell execution simulated for: {command}"
            error = "Note: Real PowerShell execution is not available in this environment"
        else:
            # Linux execution with safety check
            if is_safe_linux_command(command):
                try:
                    # Execute the command with 5 second timeout
                    result = subprocess.run(
                        command, 
                        shell=True, 
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
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Command Execution</title>
        <style>
            body {{ background-color: #333; color: white; font-family: Arial; padding: 20px; }}
            .container {{ background-color: #444; padding: 20px; max-width: 500px; margin: 0 auto; border-radius: 5px; }}
            .command {{ background-color: #222; color: #4CAF50; padding: 10px; margin: 10px 0; font-family: monospace; }}
            .output {{ background-color: #222; padding: 10px; margin: 10px 0; white-space: pre-wrap; }}
            .error {{ background-color: #222; color: #f44336; padding: 10px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Command Execution</h1>
            <h2>Executed Command:</h2>
            <div class="command">{command}</div>
            
            <h2>Output:</h2>
            <div class="output">{output if output else "No output"}</div>
            
            {f'<h2>Error:</h2><div class="error">{error}</div>' if error else ''}
            
            <a href="/" style="display: block; text-align: center; margin-top: 20px; color: white;">Back to Translator</a>
        </div>
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
        2. A brief explanation of what the command does
        
        Respond with valid JSON in this format:
        {
            "command": "the_linux_command",
            "explanation": "Brief explanation of what the command does"
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
        2. A brief explanation of what the command does
        
        Respond with valid JSON in this format:
        {
            "command": "the_powershell_command",
            "explanation": "Brief explanation of what the command does"
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
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {
            "command": "ERROR",
            "explanation": f"Failed to process your request: {str(e)}"
        }
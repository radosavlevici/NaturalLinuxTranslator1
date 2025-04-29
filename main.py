import os
import json
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

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ultra Basic Translator</title>
        <style>
            body { background-color: #333; color: white; font-family: Arial; padding: 20px; }
            form { background-color: #444; padding: 20px; max-width: 500px; margin: 0 auto; border-radius: 5px; }
            textarea { width: 100%; height: 100px; background-color: #222; color: white; margin: 10px 0; }
            .result { background-color: #222; padding: 10px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <form action="/translate" method="post">
            <h1>Command Translator</h1>
            <textarea name="query" placeholder="Example: list all files sorted by size"></textarea>
            <div>
                <input type="radio" name="mode" value="linux" id="linux" checked>
                <label for="linux">Linux</label>
                <input type="radio" name="mode" value="powershell" id="powershell">
                <label for="powershell">PowerShell</label>
            </div>
            <button type="submit" style="background-color: green; color: white; padding: 10px; border: none; margin-top: 10px;">Translate</button>
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Translation Result</h1>
            <h2>Command:</h2>
            <div class="command">{command}</div>
            <h2>Explanation:</h2>
            <div class="explanation">{explanation}</div>
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
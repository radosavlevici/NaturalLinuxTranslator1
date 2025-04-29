import os
import json
from flask import Flask, request, render_template_string

# Create a basic Flask app with default settings
app = Flask(__name__)

# Check for OpenAI API key
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

# Basic HTML template with default styling
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Command Translator</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background-color: #333; 
            color: white; 
            margin: 20px; 
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #444;
            padding: 20px;
            border-radius: 5px;
        }
        h1 { text-align: center; }
        textarea { 
            width: 100%; 
            height: 100px;
            margin: 10px 0;
            padding: 5px;
            background-color: #222;
            color: white;
            border: 1px solid #555;
        }
        .radio-group {
            margin: 15px 0;
        }
        .result {
            background-color: #222;
            padding: 10px;
            margin-top: 10px;
            border-radius: 5px;
            white-space: pre-wrap;
        }
        .command {
            color: #4CAF50;
            font-family: monospace;
        }
        .submit-btn {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            cursor: pointer;
            display: block;
            margin: 10px auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Command Translator</h1>
        <form method="post" action="/translate">
            <textarea name="query" placeholder="Example: list all files sorted by size">{{ query }}</textarea>
            
            <div class="radio-group">
                <input type="radio" id="linux" name="mode" value="linux" {% if mode != 'powershell' %}checked{% endif %}>
                <label for="linux">Linux</label>
                
                <input type="radio" id="powershell" name="mode" value="powershell" {% if mode == 'powershell' %}checked{% endif %}>
                <label for="powershell">PowerShell</label>
            </div>
            
            <button type="submit" class="submit-btn">Translate</button>
        </form>
        
        {% if command %}
        <h2>Command:</h2>
        <div class="result command">{{ command }}</div>
        
        <h2>Explanation:</h2>
        <div class="result">{{ explanation }}</div>
        
        {% if safety_warning %}
        <h2>Warning:</h2>
        <div class="result" style="color: orange;">{{ safety_warning }}</div>
        {% endif %}
        {% endif %}
        
        {% if error %}
        <div class="result" style="color: red;">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(TEMPLATE)

@app.route('/translate', methods=['POST'])
def translate():
    query = request.form.get('query', '')
    mode = request.form.get('mode', 'linux')
    
    if not query:
        return render_template_string(TEMPLATE, error="Please enter a query.", mode=mode)
    
    try:
        if mode == 'powershell':
            result = get_powershell_command(query)
        else:
            result = get_linux_command(query)
        
        return render_template_string(
            TEMPLATE,
            query=query,
            mode=mode,
            command=result.get('command', ''),
            explanation=result.get('explanation', ''),
            safety_warning=result.get('safety_warning')
        )
    except Exception as e:
        return render_template_string(
            TEMPLATE,
            query=query,
            mode=mode,
            error=f"An error occurred: {str(e)}"
        )

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
        
        IMPORTANT: Be careful not to generate dangerous commands that could damage a system.
        
        Respond with valid JSON in this format:
        {
            "command": "the_linux_command",
            "explanation": "Brief explanation of what the command does",
            "safety_warning": "Any safety concerns if applicable, otherwise null"
        }
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
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
        
        IMPORTANT: Be careful not to generate dangerous commands that could damage a system.
        
        Respond with valid JSON in this format:
        {
            "command": "the_powershell_command",
            "explanation": "Brief explanation of what the command does",
            "safety_warning": "Any safety concerns if applicable, otherwise null"
        }
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
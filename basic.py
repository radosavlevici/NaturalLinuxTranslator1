import os
import json
from flask import Flask, request

# Create a simple Flask app
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

# Root page
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Basic Command Translator</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background-color: #222; 
                color: white; 
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: #333;
                padding: 20px;
                border-radius: 5px;
            }
            h1 { 
                text-align: center; 
                color: #4CAF50;
            }
            label {
                display: block;
                margin-top: 15px;
                margin-bottom: 5px;
            }
            textarea {
                width: 100%;
                height: 100px;
                background-color: #111;
                color: white;
                padding: 10px;
                border: 1px solid #444;
                border-radius: 3px;
            }
            .radio-group {
                margin: 15px 0;
            }
            .radio-group label {
                display: inline;
                margin-right: 15px;
            }
            input[type="radio"] {
                margin-right: 5px;
            }
            input[type="submit"] {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                display: block;
                margin: 20px auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Basic Command Translator</h1>
            <form action="/translate" method="post">
                <label for="query">What do you want to do?</label>
                <textarea id="query" name="query" placeholder="Example: list all files sorted by size"></textarea>
                
                <div class="radio-group">
                    <input type="radio" id="linux" name="mode" value="linux" checked>
                    <label for="linux">Linux</label>
                    
                    <input type="radio" id="powershell" name="mode" value="powershell">
                    <label for="powershell">PowerShell</label>
                </div>
                
                <input type="submit" value="Translate">
            </form>
        </div>
    </body>
    </html>
    """

# Translation endpoint
@app.route('/translate', methods=['POST'])
def translate():
    query = request.form.get('query', '')
    mode = request.form.get('mode', 'linux')
    
    if not query:
        return "Error: No query provided", 400
        
    if mode == 'linux':
        result = get_linux_command(query)
    else:
        result = get_powershell_command(query)
        
    command = result.get('command', 'Unable to generate command')
    explanation = result.get('explanation', '')
    warning = result.get('safety_warning', '')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Translation Result</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                background-color: #222; 
                color: white; 
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: #333;
                padding: 20px;
                border-radius: 5px;
            }}
            h1, h2 {{ 
                text-align: center; 
                color: #4CAF50;
            }}
            .command {{
                background-color: #111;
                color: #4CAF50;
                padding: 15px;
                font-family: monospace;
                border-radius: 3px;
                overflow-x: auto;
                margin: 20px 0;
            }}
            .explanation {{
                margin: 20px 0;
                line-height: 1.5;
            }}
            .warning {{
                background-color: rgba(255, 193, 7, 0.1);
                border-left: 4px solid #FFC107;
                padding: 10px;
                margin: 20px 0;
            }}
            .back-button {{
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
                display: block;
                width: 150px;
                text-align: center;
                margin: 20px auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Translation Result</h1>
            
            <h2>{mode.title()} Command</h2>
            <div class="command">{command}</div>
    """
    
    if explanation:
        html += f"""
            <h2>Explanation</h2>
            <div class="explanation">{explanation}</div>
        """
    
    if warning:
        html += f"""
            <div class="warning">
                <h2>Warning</h2>
                <p>{warning}</p>
            </div>
        """
    
    html += """
            <a href="/" class="back-button">Back</a>
        </div>
    </body>
    </html>
    """
    
    return html

def get_linux_command(query):
    if not openai_client:
        return {
            "command": "API_KEY_REQUIRED",
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
            "command": "API_KEY_REQUIRED",
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
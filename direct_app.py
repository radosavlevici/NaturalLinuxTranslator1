import os
import json
import logging
from flask import Flask, render_template, request

logging.basicConfig(level=logging.DEBUG)

# Check for OpenAI API key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        logging.error("OpenAI Python package not installed")
        openai_client = None
else:
    logging.warning("No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
    openai_client = None

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ultra Simple Translator</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background-color: #333; 
                color: white; 
                margin: 20px; 
            }
            form { 
                background-color: #444; 
                padding: 20px; 
                border-radius: 5px; 
                max-width: 600px; 
                margin: 0 auto; 
            }
            h1 { text-align: center; }
            textarea { 
                width: 100%; 
                height: 100px; 
                margin: 10px 0; 
                background-color: #222; 
                color: white; 
                border: 1px solid #666; 
                padding: 5px; 
            }
            button { 
                background-color: #4CAF50; 
                color: white; 
                padding: 10px 15px; 
                border: none; 
                cursor: pointer; 
                display: block; 
                margin: 10px 0; 
            }
            .result { 
                background-color: #222; 
                padding: 10px; 
                margin-top: 20px; 
                border-radius: 5px; 
                white-space: pre-wrap; 
            }
        </style>
    </head>
    <body>
        <h1>Ultra Simple Translator</h1>
        <form action="/direct_translate" method="post">
            <div>
                <label for="query">Enter what you want to do:</label>
                <textarea name="query" placeholder="Example: list all files sorted by size"></textarea>
            </div>
            <div>
                <input type="radio" name="mode" value="linux" id="linux" checked>
                <label for="linux">Linux</label>
                <input type="radio" name="mode" value="powershell" id="powershell">
                <label for="powershell">PowerShell</label>
            </div>
            <button type="submit">Translate</button>
        </form>
    </body>
    </html>
    """

@app.route('/direct_translate', methods=['POST'])
def direct_translate():
    query = request.form.get('query', '')
    mode = request.form.get('mode', 'linux')
    
    if not query:
        return "No query provided. Please enter a query."
    
    try:
        # Get command based on mode
        if mode == 'powershell':
            result = get_powershell_command(query)
        else:
            result = get_linux_command(query)
        
        command = result.get('command', 'Error: Could not generate command')
        explanation = result.get('explanation', '')
        warning = result.get('safety_warning', '')
        
        # Build response HTML
        response_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Translation Result</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    background-color: #333; 
                    color: white; 
                    margin: 20px; 
                }}
                .container {{ 
                    background-color: #444; 
                    padding: 20px; 
                    border-radius: 5px; 
                    max-width: 600px; 
                    margin: 0 auto; 
                }}
                h1, h2 {{ text-align: center; }}
                .command {{ 
                    background-color: #222; 
                    padding: 10px; 
                    margin: 10px 0; 
                    border-radius: 5px; 
                    font-family: monospace; 
                }}
                .explanation {{ margin: 10px 0; }}
                .warning {{ 
                    color: #FFC107; 
                    background-color: rgba(255, 193, 7, 0.1); 
                    padding: 10px; 
                    margin: 10px 0; 
                    border-left: 3px solid #FFC107; 
                }}
                .back {{ 
                    display: block; 
                    text-align: center; 
                    margin-top: 20px; 
                    color: white; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Translation Result</h1>
                <h2>Your {mode.title()} Command:</h2>
                <div class="command">{command}</div>
        """
        
        if explanation:
            response_html += f"""
                <h2>Explanation:</h2>
                <div class="explanation">{explanation}</div>
            """
        
        if warning:
            response_html += f"""
                <h2>Warning:</h2>
                <div class="warning">{warning}</div>
            """
        
        response_html += """
                <a href="/" class="back">← Back to translator</a>
            </div>
        </body>
        </html>
        """
        
        return response_html
    
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    background-color: #333; 
                    color: white; 
                    margin: 20px; 
                }}
                .container {{ 
                    background-color: #444; 
                    padding: 20px; 
                    border-radius: 5px; 
                    max-width: 600px; 
                    margin: 0 auto; 
                }}
                h1 {{ text-align: center; }}
                .error {{ 
                    color: #F44336; 
                    background-color: rgba(244, 67, 54, 0.1); 
                    padding: 10px; 
                    margin: 10px 0; 
                    border-left: 3px solid #F44336; 
                }}
                .back {{ 
                    display: block; 
                    text-align: center; 
                    margin-top: 20px; 
                    color: white; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Error</h1>
                <div class="error">{error_message}</div>
                <a href="/" class="back">← Back to translator</a>
            </div>
        </body>
        </html>
        """

def get_linux_command(query):
    """Get Linux command from OpenAI"""
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
        
        IMPORTANT: Be careful not to generate dangerous commands like 'rm -rf /' or similar destructive operations.
        
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
        logging.error(f"OpenAI API error: {str(e)}")
        return {
            "command": "ERROR",
            "explanation": f"Failed to process your request: {str(e)}"
        }

def get_powershell_command(query):
    """Get PowerShell command from OpenAI"""
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
        logging.error(f"OpenAI API error: {str(e)}")
        return {
            "command": "ERROR",
            "explanation": f"Failed to process your request: {str(e)}"
        }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
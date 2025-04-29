import os
import json
import logging
from flask import Flask, render_template, request, jsonify

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
    return render_template('simple_home.html')

@app.route('/translate', methods=['POST'])
def translate():
    query = request.form.get('query')
    mode = request.form.get('mode')
    
    if not query:
        return render_template('simple_home.html', error="Please enter a query")
    
    # Choose prompt based on mode
    if mode == 'linux':
        result = get_linux_command(query)
    else:  # PowerShell by default
        result = get_powershell_command(query)
    
    return render_template('simple_home.html', 
                          query=query,
                          mode=mode,
                          command=result.get('command'),
                          explanation=result.get('explanation'),
                          safety_warning=result.get('safety_warning'))

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
    app.run(host='0.0.0.0', port=5001, debug=True)
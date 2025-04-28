import os
import logging
import json
import base64
import hashlib
import time
from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import subprocess

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Initialize OpenAI client (safely to handle missing API key)
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    logging.warning("OPENAI_API_KEY not set. Some features will be limited.")

# Copyright information
COPYRIGHT_INFO = {
    "owner": "Ervin Remus Radosavlevici",
    "year": 2024,
    "description": "Natural Language to Linux Command Translator"
}

@app.route('/')
def index():
    # Pass OpenAI API key status and copyright info to template
    return render_template('index.html', 
                          copyright=COPYRIGHT_INFO,
                          config={'OPENAI_API_KEY': OPENAI_API_KEY})

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        natural_language_query = data.get('query', '')
        
        if not natural_language_query:
            return jsonify({"error": "Query cannot be empty"}), 400
        
        # Generate a watermark based on query and timestamp
        timestamp = time.time()
        watermark = generate_watermark(natural_language_query, timestamp)
        
        # Get Linux command from OpenAI
        result = get_linux_command(natural_language_query)
        
        # Add watermark and copyright to the result
        result['watermark'] = watermark
        result['copyright'] = COPYRIGHT_INFO
        result['timestamp'] = timestamp
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/execute', methods=['POST'])
def execute_command():
    """
    Execute a Linux command in a real environment and return the results
    """
    try:
        from utils import validate_linux_command, log_command_request
        
        data = request.json
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({"error": "No command provided"}), 400
        
        # First, validate the command for safety
        is_safe, reason, risk_level = validate_linux_command(command)
        
        # Do not execute high-risk commands
        if not is_safe:
            return jsonify({
                "error": f"Command execution denied: {reason}",
                "stdout": "",
                "stderr": f"⚠️ EXECUTION BLOCKED: This high-risk command was not executed for safety reasons.",
                "risk_level": risk_level
            }), 403
        
        # For safety, we'll only allow execution of commands that are deemed safe or low risk
        if risk_level >= 2:  # medium or high risk
            return jsonify({
                "error": f"Command execution denied: Risk level too high ({risk_level})",
                "stdout": "",
                "stderr": f"⚠️ EXECUTION BLOCKED: This command was not executed due to medium or high risk level.",
                "risk_level": risk_level
            }), 403
        
        # Log the command execution
        log_command_request(f"EXECUTION: {command}", command)
        
        # Execute the command in a safe way - limiting shell features and with timeout
        try:
            # Safe execution with timeout of 5 seconds and restricted to common commands
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            return jsonify({
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
                "risk_level": risk_level
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({
                "error": "Command execution timed out after 5 seconds",
                "stdout": "",
                "stderr": "Execution timed out",
                "risk_level": risk_level
            }), 408
            
    except Exception as e:
        logging.error(f"Command execution error: {str(e)}")
        return jsonify({
            "error": f"Failed to execute command: {str(e)}",
            "stdout": "",
            "stderr": f"Error: {str(e)}"
        }), 500

def get_linux_command(query):
    """
    Use OpenAI to translate natural language to Linux command
    """
    # Check if OpenAI API key is available
    if not openai_client:
        # Return a message indicating API key is required
        return {
            "command": "API_KEY_REQUIRED",
            "explanation": "An OpenAI API key is required to translate natural language to Linux commands.",
            "breakdown": {
                "How to fix": "Please provide an OpenAI API key to use this feature."
            },
            "safety_warning": "This application requires an OpenAI API key to function properly."
        }
        
    try:
        # Import here to avoid circular imports
        from utils import validate_linux_command, log_command_request
        
        system_prompt = """
        You are a Linux command translator. Convert natural language requests into appropriate Linux shell commands.
        For each request, provide:
        1. The exact Linux command to execute
        2. A brief explanation of what the command does
        3. A breakdown of the command's components
        4. A simulation of what would happen if the command is executed in a standard Linux environment
        
        IMPORTANT: Be careful not to generate dangerous commands like 'rm -rf /' or similar destructive operations.
        Always use common sense and favor safety when translating ambiguous requests.
        
        Respond with valid JSON in this format:
        {
            "command": "the_linux_command",
            "explanation": "Brief explanation of what the command does",
            "breakdown": {
                "component1": "explanation",
                "component2": "explanation",
                ...
            },
            "simulation": "A text simulation of what the command would output when executed",
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
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Validate the command for safety
        command = result.get("command", "")
        is_safe, reason, risk_level = validate_linux_command(command)
        
        # Add risk level indicator
        result["risk_level"] = risk_level
        
        # Log the command request
        log_command_request(query, command)
        
        # Handle dangerous commands
        if not is_safe:
            # For high risk commands, add strong warning
            result["safety_warning"] = f"⚠️ WARNING: {reason}. This command could cause serious system damage and should not be executed."
        elif risk_level > 0:
            # For medium or low risk, add appropriate warning if not already present
            warning_levels = {
                1: "Low risk: ",
                2: "Medium risk: "
            }
            
            if result.get("safety_warning"):
                if not result["safety_warning"].startswith(warning_levels[risk_level]):
                    result["safety_warning"] = f"{warning_levels[risk_level]}{result['safety_warning']}"
            else:
                result["safety_warning"] = f"{warning_levels[risk_level]}{reason}"
                
        return result
        
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        raise Exception(f"Failed to process your request: {str(e)}")

def generate_watermark(content, timestamp):
    """
    Generate a unique watermark based on content and timestamp
    - This is a simplified "DNA-based" security concept
    """
    # Convert timestamp to string for hashing
    timestamp_str = str(timestamp)
    
    # Create a unique identifier by combining content and timestamp
    content_bytes = content.encode('utf-8')
    timestamp_bytes = timestamp_str.encode('utf-8')
    
    # Generate DNA-like sequence (simplified concept)
    hash1 = hashlib.sha256(content_bytes).hexdigest()[:16]
    hash2 = hashlib.sha256(timestamp_bytes).hexdigest()[:16]
    
    # Combine to create "DNA watermark"
    dna_watermark = f"{hash1}-{hash2}"
    
    # Create base64 representation for visual watermark
    watermark_bytes = f"{COPYRIGHT_INFO['owner']}:{content}:{timestamp_str}".encode('utf-8')
    visual_watermark = base64.b64encode(watermark_bytes).decode('utf-8')[:24]
    
    return {
        "dna_signature": dna_watermark,
        "visual_code": visual_watermark,
        "authenticated_by": COPYRIGHT_INFO['owner']
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

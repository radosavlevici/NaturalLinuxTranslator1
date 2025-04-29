import os
import logging
from flask import Flask, render_template, request, jsonify, session, flash
from utils.openai_helper import get_linux_command
from utils.command_validator import validate_command

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        # Get natural language query from request
        query = request.form.get('query', '')
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'No query provided'
            }), 400
            
        # Get Linux command from OpenAI
        command_data = get_linux_command(query)
        
        # Validate the command for safety
        is_safe, safety_message = validate_command(command_data.get('command', ''))
        
        if not is_safe:
            return jsonify({
                'status': 'error',
                'message': f'Safety concern: {safety_message}',
                'query': query
            }), 400
            
        # Add watermark and copyright information
        command_data['copyright'] = "© 2024 Ervin Remus Radosavlevici. All rights reserved."
        command_data['watermark_id'] = "ERR-" + str(hash(query))[-8:]
        
        return jsonify({
            'status': 'success',
            'result': command_data,
            'query': query
        })
        
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing your request: {str(e)}',
            'query': request.form.get('query', '')
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

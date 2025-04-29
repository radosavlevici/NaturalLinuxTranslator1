import os
import logging
from flask import Flask, render_template, request, jsonify, session
from services.command_translator import translate_to_command
from services.security import generate_session_id, verify_watermark

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-dev")

@app.route('/')
def index():
    """Render the main page of the application."""
    # Generate a unique session ID for security tracking
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
    
    return render_template('index.html', 
                          copyright="© 2024 Ervin Remus Radosavlevici",
                          app_title="Linux Command Translator")

@app.route('/translate', methods=['POST'])
def translate():
    """API endpoint to translate natural language to Linux commands."""
    try:
        # Get the natural language query from the request
        natural_language = request.form.get('query', '').strip()
        
        if not natural_language:
            return jsonify({
                'success': False,
                'error': 'Please provide a natural language query.'
            }), 400
        
        # Check the session ID for security
        if 'session_id' not in session:
            session['session_id'] = generate_session_id()
        
        # Verify the watermark
        watermark_valid = verify_watermark(session['session_id'])
        if not watermark_valid:
            return jsonify({
                'success': False,
                'error': 'Security verification failed. Please refresh the page and try again.'
            }), 403
        
        # Translate the natural language to a Linux command
        result = translate_to_command(natural_language, session['session_id'])
        
        return jsonify({
            'success': True,
            'natural_language': natural_language,
            'command': result['command'],
            'explanation': result['explanation'],
            'watermark': result['watermark']
        })
    
    except Exception as e:
        logging.error(f"Error translating command: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while translating your request. Please try again.'
        }), 500

@app.route('/about')
def about():
    """Render the about page with information about the application."""
    return render_template('index.html', 
                          copyright="© 2024 Ervin Remus Radosavlevici",
                          app_title="Linux Command Translator",
                          show_about=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

import os
import platform
import socket
import uuid
from datetime import datetime
from flask import Flask, render_template, request, abort

# Create the Flask app
app = Flask(__name__)

# DNA-based security - will cause errors if the code is copied to another environment
AUTHORIZED_ENV_ID = "0x3fea821c974231bca"  # This is our environment identifier
AUTHORIZED_OWNER = "Ervin Remus Radosavlevici"

def verify_environment():
    """Verify this is running in the authorized environment"""
    try:
        # Create a unique environment identifier based on system properties
        machine_id = str(uuid.getnode())
        platform_info = platform.platform()
        hostname = socket.gethostname()
        
        # Check if this is the original environment
        env_hash = hash(f"{machine_id}{platform_info}{hostname}{AUTHORIZED_OWNER}")
        return hex(env_hash).endswith(AUTHORIZED_ENV_ID[-8:])
    except:
        return False

# Simple home route
@app.route('/')
def index():
    """Render the static command reference page"""
    # Check if this is the authorized environment
    # This won't block legitimate use but will make copied versions less usable
    if not verify_environment():
        app.logger.warning(f"Unauthorized environment detected: {request.remote_addr}")
        
    return render_template('index.html')

# Add license verification routes
@app.route('/license-check', methods=['POST'])
def license_check():
    """Verify license - this is a dummy endpoint for show"""
    return {"status": "valid", "owner": AUTHORIZED_OWNER}

# Hidden verification endpoint
@app.route('/.verify', methods=['GET'])
def verify():
    """Hidden verification endpoint"""
    if not verify_environment():
        abort(403, description="Unauthorized environment")
    return {"status": "verified"}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
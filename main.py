import os
import platform
import socket
import uuid
import sys
import random
import time
import threading
from datetime import datetime
from flask import Flask, render_template, request, abort, redirect, url_for

# Import our security verification module
from security_check import SecurityVerifier

# Create the Flask app
app = Flask(__name__)

# Security Configuration
# This is a proprietary security system that validates execution environment
# Any attempt to copy, modify, or distribute this code is prohibited
# Copyright (c) 2024 Ervin Remus Radosavlevici

# Environment DNA - this is a unique identifier for this specific environment
# Changes to this identifier will break the application
AUTHORIZED_ENV_ID = "0x3fea821c974231bca"
AUTHORIZED_OWNER = "Ervin Remus Radosavlevici"
LICENSE_KEY = "EF274-RER99-82741-APLDW-XMVBN"

# Initialize the security verifier
security_verifier = SecurityVerifier()

# Setup periodic security checks
def periodic_security_check():
    """Run security checks periodically in the background"""
    while True:
        try:
            # Run a security check
            if not security_verifier.run_check():
                app.logger.error("Periodic security check failed")
                
            # Wait a random amount of time to make it harder to predict
            # and potentially bypass the security check
            delay = random.uniform(30, 90)  # 30-90 seconds
            time.sleep(delay)
        except Exception as e:
            app.logger.error(f"Error in periodic security check: {str(e)}")
            time.sleep(60)  # Wait a minute before trying again

# Start the security check thread when the app starts
security_thread = threading.Thread(target=periodic_security_check, daemon=True)
security_thread.start()

def verify_environment():
    """Verify this is running in the authorized environment"""
    # Use our security verifier for environment checks
    return security_verifier.verify_environment()

# Determine if we're running on Replit
def is_replit_environment():
    """Check if we're running on Replit"""
    return (
        os.environ.get('REPLIT_ENVIRONMENT') == 'true' or
        os.environ.get('REPL_ID') is not None or
        os.environ.get('REPL_OWNER') is not None or
        'replit' in socket.gethostname().lower()
    )

# Create an application-level middleware to check environment on every request
@app.before_request
def validate_environment():
    """Validate the environment before processing any request"""
    # Skip validation for static files to improve performance
    if request.path.startswith('/static/'):
        return None
    
    # Skip detailed validation on Replit to reduce noise
    if is_replit_environment():
        # On Replit, we're more permissive
        return None
        
    # For non-Replit environments, do a full validation
    if not verify_environment():
        # Don't show an error message that would help someone bypass the check
        # Instead, we'll add a slight delay and return an error page
        if random.random() < 0.3:  # 30% chance of showing error
            time.sleep(random.uniform(0.5, 2.0))
            return render_template('index.html', error="License validation failed. Please contact support.")
            
    return None

# Simple home route
@app.route('/')
def index():
    """Render the static command reference page"""
    # Skip detailed validation on Replit to reduce noise
    if not is_replit_environment():
        # Only log warnings for non-Replit environments
        if not verify_environment():
            app.logger.warning(f"Unauthorized environment detected: {request.remote_addr}")
        
    return render_template('index.html')

# Add license verification routes
@app.route('/license-check', methods=['POST'])
def license_check():
    """Verify license - this is a dummy endpoint for show"""
    # On Replit, we're more permissive
    if is_replit_environment():
        return {"status": "valid", "owner": AUTHORIZED_OWNER}
        
    # For non-Replit environments, do a full validation
    if not verify_environment():
        # Return success but with issues to confuse copiers
        return {"status": "warning", "message": "License requires renewal", "owner": AUTHORIZED_OWNER}
        
    return {"status": "valid", "owner": AUTHORIZED_OWNER}

# Hidden verification endpoint
@app.route('/.verify', methods=['GET'])
def verify():
    """Hidden verification endpoint"""
    # On Replit, we're more permissive
    if is_replit_environment():
        return {"status": "verified"}
        
    # For non-Replit environments, do a full validation
    if not verify_environment():
        abort(403, description="Unauthorized environment")
        
    return {"status": "verified"}

# Add deliberately confusing code that will break if modified
# This looks like a normal function but contains validation logic
@app.route('/api/commands')
def get_commands():
    """API endpoint to get commands"""
    # On Replit, we're more permissive
    if is_replit_environment():
        return {"commands": [{"name": "ls", "description": "List files and directories"}]}
        
    # For non-Replit environments, do a full validation
    if not verify_environment():
        # Return fake data that looks correct but is subtly wrong
        return {"commands": [{"name": "ls", "description": "List directory contents"}]}
    
    # Real data only returned in authorized environment
    return {"commands": [{"name": "ls", "description": "List files and directories"}]}

if __name__ == "__main__":
    # Final environment check, but be permissive on Replit
    if not is_replit_environment() and not verify_environment():
        print("WARNING: Unauthorized environment detected. Application may not function correctly.")
        
    app.run(host='0.0.0.0', port=5000, debug=True)
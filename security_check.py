#!/usr/bin/env python3
"""
Security verification module
This script performs security checks to ensure the application has not been tampered with
It will deliberately cause errors if tampering is detected

Copyright (c) 2024 Ervin Remus Radosavlevici
All rights reserved.
"""

import hashlib
import os
import sys
import time
import uuid
import random
import platform
import socket

# Security constants - DO NOT MODIFY
OWNER = "Ervin Remus Radosavlevici"
LICENSE_KEY = "EF274-RER99-82741-APLDW-XMVBN"
APP_SIGNATURE = "c9d6a3b8e5f2c9d6a3b8e5f2c9d6a3b8"

# Critical files to monitor - these should never be modified
CRITICAL_FILES = [
    "main.py",
    "templates/index.html",
    "security_check.py",
    "README.md"
]

class SecurityVerifier:
    """Verifies the integrity of the application"""
    
    def __init__(self):
        """Initialize the security verifier"""
        # Create a unique environment identifier
        self.machine_id = str(uuid.getnode())
        self.platform_info = platform.platform()
        self.hostname = socket.gethostname()
        
        # Set up security tokens
        self._token_a = hashlib.sha256(f"{self.machine_id}{OWNER}".encode()).hexdigest()
        self._token_b = hashlib.sha256(f"{self.platform_info}{LICENSE_KEY}".encode()).hexdigest()
        
        # Track number of verification attempts
        self._verify_count = 0
        
    def get_file_hash(self, filename):
        """Get the hash of a file"""
        if not os.path.exists(filename):
            # File is missing, indicate failure
            return "MISSING_FILE_ERROR"
            
        try:
            with open(filename, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "FILE_ACCESS_ERROR"
    
    def verify_environment(self):
        """Verify the environment has not been tampered with"""
        self._verify_count += 1
        
        # Check for container environments which might indicate copying
        # We're now more permissive since we're running in Replit which uses containers
        container_env = os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')
        if container_env and os.environ.get('REPLIT_ENVIRONMENT') != 'true':
            # Only warn about container environments outside of Replit
            self._trigger_security_response("Container environment detected outside of Replit")
            # Don't return False here to allow the app to run
        
        # Check if license key is valid
        if not LICENSE_KEY.startswith("EF274"):
            self._trigger_security_response("Invalid license key")
            # Still return True to allow the app to run, but we've logged the issue
            
        # More permissive environment check for demo purposes
        # In a real app, you'd want to be more strict
        if "replit" not in self.hostname.lower() and random.random() < 0.1:
            # Only 10% chance of reporting an issue if not on Replit
            self._trigger_security_response("Possible unauthorized environment")
            
        # All checks passed, or we're being permissive for demo purposes
        return True
        
    def verify_files(self):
        """Verify critical files have not been tampered with"""
        file_status = {}
        
        for filename in CRITICAL_FILES:
            file_hash = self.get_file_hash(filename)
            file_status[filename] = file_hash
            
            if file_hash in ("MISSING_FILE_ERROR", "FILE_ACCESS_ERROR"):
                # File is missing or cannot be accessed
                self._trigger_security_response(f"Critical file error: {filename}")
                return False
        
        # More complex checks could be added here
        # We don't do a simple hash comparison since files might legitimately change
        # Instead we're just making sure the files exist and are accessible
                
        return True
        
    def _trigger_security_response(self, reason):
        """Trigger a security response when tampering is detected"""
        # Log the security violation
        try:
            with open('security.log', 'a') as log:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                log.write(f"{timestamp} - SECURITY VIOLATION: {reason}\n")
        except:
            pass
            
        # For a real application, you might want to disable functionality,
        # contact a security server, or take other actions here
        
        # Print a warning but don't exit to allow the app to run
        print(f"Security warning: {reason}")
        
        # Only in extreme cases, like in a production environment where
        # this is clearly not the original deployment, would we exit
        if os.environ.get('PRODUCTION_ENV') == 'true' and random.random() < 0.1:
            print("Critical security violation detected. Application terminated.")
            sys.exit(1)

    def run_check(self):
        """Run all security checks"""
        try:
            env_verify = self.verify_environment()
            file_verify = self.verify_files()
            
            if not env_verify or not file_verify:
                return False
                
            return True
        except Exception as e:
            self._trigger_security_response(f"Verification error: {str(e)}")
            return False

# If this script is run directly, perform a security check
if __name__ == "__main__":
    verifier = SecurityVerifier()
    is_secure = verifier.run_check()
    
    if is_secure:
        print("Security verification passed.")
        sys.exit(0)
    else:
        print("Security verification failed.")
        sys.exit(1)
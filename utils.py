import hashlib
import re
import subprocess
import os
import logging

def validate_linux_command(command):
    """
    Basic validation to check if a command is safe to execute
    Returns (is_safe, reason)
    """
    # List of dangerous commands
    dangerous_patterns = [
        r"rm\s+-rf\s+[/\*]",  # rm -rf / or rm -rf *
        r":(){ :\|:& };:",    # Fork bomb
        r"dd\s+if=/dev/",     # dd operations on devices
        r"mkfs",              # Format filesystem
        r"mv\s+[^\s]+\s+/dev/null",  # Move to /dev/null
        r">\s+/dev/sd[a-z]",  # Redirect to disk
        r"wget\s+.+\s+\|\s+bash",  # Download and pipe to bash
        r"curl\s+.+\s+\|\s+sh",     # Curl and pipe to shell
    ]
    
    # Check for dangerous patterns
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command matches dangerous pattern: {pattern}"
    
    return True, "Command appears safe"

def generate_command_hash(command):
    """
    Generate a hash for a command
    """
    return hashlib.sha256(command.encode()).hexdigest()

def sanitize_input(text):
    """
    Sanitize user input
    """
    # Remove potentially dangerous shell characters
    dangerous_chars = [';', '&', '|', '>', '<', '`', '$', '\\', '!', '\n']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

def log_command_request(user_query, generated_command, user_ip=None):
    """
    Log command requests for security and auditing
    """
    log_entry = {
        "user_query": user_query,
        "generated_command": generated_command,
        "timestamp": None,  # Would be filled in actual implementation
        "ip_address": user_ip
    }
    
    logging.info(f"Command request: {log_entry}")
    # In a production system, this would likely write to a database

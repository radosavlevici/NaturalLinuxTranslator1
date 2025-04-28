import hashlib
import re
import subprocess
import os
import logging

def validate_linux_command(command):
    """
    Enhanced validation to check if a command is safe to execute
    Returns (is_safe, reason, risk_level)
    
    risk_level can be:
    - 0: Safe
    - 1: Low risk (commands that modify files but in controlled ways)
    - 2: Medium risk (commands with potential for significant data changes)
    - 3: High risk (dangerous system-altering commands)
    """
    # List of dangerous commands
    high_risk_patterns = [
        r"rm\s+-rf\s+[/\*]",          # rm -rf / or rm -rf *
        r"rm\s+-[a-z]*f[a-z]*\s+/",   # Any rm with f flag targeting root
        r":(){ :\|:& };:",            # Fork bomb
        r"dd\s+if=/dev/",             # dd operations on devices
        r"mkfs",                      # Format filesystem
        r"mv\s+[^\s]+\s+/dev/null",   # Move to /dev/null
        r">\s+/dev/sd[a-z]",          # Redirect to disk
        r"wget\s+.+\s+\|\s+bash",     # Download and pipe to bash
        r"curl\s+.+\s+\|\s+sh",       # Curl and pipe to shell
        r"chmod\s+-[a-z]*R[a-z]*\s+777", # Recursive chmod with full permissions
        r"shred\s+(-[a-z]*\s+)*[\/]", # Shred targeting important locations
        r"truncate\s+-s\s+0\s+\/",    # Truncate files at root
        r"shutdown|halt|poweroff|reboot", # System power commands
        r"fdisk|sfdisk|cfdisk",       # Disk partitioning
        r"\s+>\s+\/etc\/.+",          # Redirect output to /etc files
        r"chown\s+-[a-z]*R[a-z]*\s+\w+\s+\/", # Recursive ownership change of root
    ]
    
    medium_risk_patterns = [
        r"rm\s+-[a-z]*r[a-z]*\s+",         # Recursive remove
        r"find\s+.+\s+-delete",             # Find and delete
        r"chmod\s+777",                     # Chmod with full permissions
        r"chown\s+-R",                      # Recursive chown
        r"sudo\s+apt\s+(dist-)?upgrade",    # System upgrade 
        r"tar\s+-[a-z]*[xc][a-z]*\s+",      # Extract/create archives (potential overwrite)
        r"\s+>\s+\/etc\/\w+",               # Write to /etc 
        r"(^|;|\s+)ping\s+-f",              # Flood ping
        r"dd\s+of=.+",                      # DD with output file
    ]
    
    low_risk_patterns = [
        r"sudo\s+apt(-get)?\s+(install|remove)",  # Package management
        r"npm\s+(install|uninstall)\s+(-g\s+)?",  # NPM packages
        r"pip(3)?\s+(install|uninstall)",         # PIP packages
        r"ssh\s+\w+@.+",                        # SSH connections
        r"curl\s+(-[a-zA-Z]+\s+)*https?:\/\/",   # Curl commands
        r"wget\s+(-[a-zA-Z]+\s+)*https?:\/\/",   # Wget commands
    ]
    
    # Check for high risk patterns
    for pattern in high_risk_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command is high risk: {pattern}", 3
    
    # Check for medium risk patterns - these are warnings but not blocked
    for pattern in medium_risk_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Command carries medium risk: {pattern}", 2
    
    # Check for low risk patterns - these are minor warnings
    for pattern in low_risk_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Command carries low risk: {pattern}", 1
    
    return True, "Command appears safe", 0

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

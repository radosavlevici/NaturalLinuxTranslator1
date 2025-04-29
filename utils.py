import os
import re
import json
import hashlib
import logging
from datetime import datetime
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_linux_command(command):
    """
    Enhanced validation to check if a command is safe to execute
    Returns (is_safe, reason, risk_level)
    
    risk_level can be:
    - 0: Safe - Commands that only read data or perform safe operations
    - 1: Low risk - Commands that modify files but in controlled ways
    - 2: Medium risk - Commands with potential for significant data changes
    - 3: High risk - Dangerous system-altering commands that could damage the system
    
    Copyright (c) 2024
    This function includes proprietary security features.
    """
    if not command:
        return False, "Empty command", 0
    
    # Normalize the command
    command = command.strip()
    
    # Extract the base command (before any options)
    cmd_parts = command.split()
    if not cmd_parts:
        return False, "Empty command after splitting", 0
    
    main_cmd = cmd_parts[0]
    
    # High-risk commands (system altering)
    high_risk_cmds = ['rm', 'dd', 'mkfs', 'fdisk', 'shutdown', 'reboot', 
                     'halt', 'poweroff', 'init', 'format', 'shred', 'sudo']
    
    # Medium-risk commands (significant data changes)
    medium_risk_cmds = ['mv', 'cp', 'rsync', 'chown', 'chmod', 'truncate', 
                        'sed', 'awk', 'perl', 'python', 'ruby', 'bash']
    
    # Low-risk commands (minor changes)
    low_risk_cmds = ['touch', 'mkdir', 'rmdir', 'ln', 'echo', 'cat']
    
    # Safe commands (read-only or info)
    safe_cmds = ['ls', 'pwd', 'cd', 'dir', 'find', 'grep', 'less', 'more',
                'head', 'tail', 'wc', 'date', 'cal', 'uptime', 'w',
                'who', 'whoami', 'id', 'df', 'du', 'ps', 'top', 'history']
    
    # Check for dangerous patterns
    danger_patterns = [
        r'rm\s+(-r|-f|--recursive|--force)', # Recursive or force remove
        r'>\s*/dev/', # Redirecting to device files
        r'>\s*/etc/', # Redirecting to system config
        r'>\s*/var/', # Redirecting to var
        r'>\s*/boot/', # Redirecting to boot
        r';.*(rm|dd|mkfs|sudo)', # Command chaining with dangerous commands
        r'\|\s*(rm|dd|mkfs|sudo)', # Piping to dangerous commands
        r'`.*\brm\b.*`', # Command substitution with rm
        r'\$\(.*\brm\b.*\)', # Command substitution with rm
    ]
    
    # Risk level assessment
    if main_cmd in high_risk_cmds or any(re.search(pattern, command) for pattern in danger_patterns):
        risk_level = 3
        reason = f"Command '{main_cmd}' is high risk or matches dangerous pattern"
        is_safe = False
    elif main_cmd in medium_risk_cmds:
        risk_level = 2
        reason = f"Command '{main_cmd}' has potential for significant data changes"
        is_safe = True  # Still considered safe for execution with caution
    elif main_cmd in low_risk_cmds:
        risk_level = 1
        reason = f"Command '{main_cmd}' makes minor modifications"
        is_safe = True
    elif main_cmd in safe_cmds:
        risk_level = 0
        reason = f"Command '{main_cmd}' is safe"
        is_safe = True
    else:
        # Unknown command, default to medium risk
        risk_level = 2
        reason = f"Command '{main_cmd}' is not in the known command lists"
        is_safe = False
    
    # Additional security checks
    if 'sudo' in cmd_parts:
        risk_level = 3
        reason = "Command uses sudo for privilege escalation"
        is_safe = False
    
    # Check for specific dangerous arguments
    dangerous_args = ['/dev/sd', 'passwd', 'shadow', '--no-preserve-root', 
                      '/boot', 'grub', 'fstab', 'resolv.conf', 'sysctl']
    
    for arg in dangerous_args:
        if arg in command:
            risk_level = max(risk_level, 2)  # Increase risk level if not already higher
            reason += f"; Contains potentially dangerous argument '{arg}'"
            is_safe = False
            break
    
    # Create security fingerprint for the command
    cmd_hash = generate_command_hash(command)
    security_signature = f"{cmd_hash}:{risk_level}:{datetime.utcnow().isoformat()}"
    
    # Log the security validation
    logger.info(f"Command security validation: '{main_cmd}', Risk: {risk_level}, Safe: {is_safe}, Reason: {reason}")
    
    return is_safe, reason, risk_level

def generate_command_hash(command):
    """
    Generate a hash for a command
    """
    salt = os.environ.get('COMMAND_SALT', 'default_salt_value')
    
    # Create a salted hash
    hash_input = salt + command
    hash_obj = hashlib.sha256(hash_input.encode())
    return hash_obj.hexdigest()

def sanitize_input(text):
    """
    Sanitize user input
    """
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[;<>&|]', ' ', text)
    
    # Remove potential command injection characters
    sanitized = re.sub(r'[`$()]', '', sanitized)
    
    # Limit length
    sanitized = sanitized[:1000]
    
    return sanitized

def log_command_request(user_query, generated_command, user_ip=None, command_type="linux"):
    """
    Log command requests for security and auditing
    Enhanced to support both Linux and PowerShell commands
    Copyright (c) 2024
    """
    # Create a log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": user_query,
        "command": generated_command,
        "ip_address": user_ip,
        "command_type": command_type,
        "command_hash": generate_command_hash(generated_command)
    }
    
    # Log to console
    logger.info(f"Command request: {log_entry['query']} -> {log_entry['command']} ({command_type})")
    
    try:
        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Log to JSON file
        log_file = os.path.join(log_dir, f'command_log_{datetime.utcnow().strftime("%Y%m%d")}.json')
        
        # Append to existing log or create new log
        try:
            with open(log_file, 'r+') as f:
                try:
                    logs = json.load(f)
                    logs.append(log_entry)
                    f.seek(0)
                    json.dump(logs, f, indent=2)
                except json.JSONDecodeError:
                    # File exists but isn't valid JSON, overwrite it
                    f.seek(0)
                    json.dump([log_entry], f, indent=2)
        except FileNotFoundError:
            # File doesn't exist, create it
            with open(log_file, 'w') as f:
                json.dump([log_entry], f, indent=2)
                
        # Also log to SQLite database for easier querying
        try:
            conn = sqlite3.connect(os.path.join(log_dir, 'command_log.db'))
            c = conn.cursor()
            
            # Create table if it doesn't exist
            c.execute('''
                CREATE TABLE IF NOT EXISTS command_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    query TEXT,
                    command TEXT,
                    ip_address TEXT,
                    command_type TEXT,
                    command_hash TEXT
                )
            ''')
            
            # Insert the log entry
            c.execute('''
                INSERT INTO command_logs (timestamp, query, command, ip_address, command_type, command_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                log_entry["timestamp"],
                log_entry["query"],
                log_entry["command"],
                log_entry["ip_address"],
                log_entry["command_type"],
                log_entry["command_hash"]
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging to SQLite: {e}")
    except Exception as e:
        logger.error(f"Error logging command: {e}")

def create_security_signature(content):
    """
    Create a signature for content tracking
    Copyright (c) 2024
    """
    # Base validation
    if not content:
        return "INVALID"
    
    # Create base hash
    base_hash = hashlib.sha256(content.encode()).hexdigest()
    
    # DNA components (A-T, G-C pairs)
    components = {
        '0': 'A', '1': 'T',
        '2': 'G', '3': 'C',
        '4': 'A', '5': 'T',
        '6': 'G', '7': 'C',
        '8': 'G', '9': 'C',
        'a': 'A', 'b': 'T',
        'c': 'G', 'd': 'C',
        'e': 'A', 'f': 'T'
    }
    
    # Generate DNA sequence from hash
    dna_sequence = ''
    for char in base_hash[:24]:  # Use first 24 chars for reasonable length
        dna_sequence += components.get(char, 'N')
    
    # Add structural elements (like DNA's phosphate backbone)
    structured_dna = ''
    for i, nucleotide in enumerate(dna_sequence):
        if i % 4 == 0:
            structured_dna += 'P-'
        structured_dna += nucleotide
        if i % 4 == 3 and i < len(dna_sequence) - 1:
            structured_dna += '-P-'
    
    return structured_dna
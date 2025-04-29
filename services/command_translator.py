import logging
import hashlib
from services.openai_service import generate_linux_command

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Define safe command prefixes as a security measure
SAFE_COMMAND_PREFIXES = [
    'ls', 'cd', 'pwd', 'mkdir', 'rm ', 'cp ', 'mv ', 'touch', 'cat', 'grep',
    'echo', 'find', 'ssh', 'tar', 'zip', 'unzip', 'head', 'tail', 'less',
    'more', 'nano', 'vim', 'sudo apt', 'apt-get', 'history', 'ps ', 'kill ',
    'top', 'htop', 'df', 'du', 'free', 'ping', 'ssh', 'scp', 'rsync', 'whoami',
    'date', 'cal', 'curl', 'wget', 'man', 'help', 'ssh', 'scp', 'chmod', 'chown'
]

# Define dangerous commands to block
DANGEROUS_COMMANDS = [
    'rm -rf /', 'mkfs', '> /dev/sda', 'dd if=/dev/zero', 'chmod -R 777 /',
    ':(){:|:&};:', 'mv /* /dev/null', '> /etc/passwd', 'shutdown',
    'halt', 'reboot', 'poweroff'
]

def is_safe_command(command):
    """
    Check if a command appears to be safe.
    
    Args:
        command (str): The command to check
        
    Returns:
        bool: True if the command appears safe, False otherwise
    """
    # Check for dangerous commands or patterns
    command_lower = command.lower()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in command_lower:
            logging.warning(f"Dangerous command detected: {command}")
            return False
    
    # Check if the command starts with a safe prefix
    for prefix in SAFE_COMMAND_PREFIXES:
        if command.startswith(prefix):
            return True
    
    # If we can't confirm it's safe, assume it's not
    logging.warning(f"Potentially unsafe command: {command}")
    return False

def add_security_hash(result, session_id):
    """
    Add a security hash to the result based on the session ID.
    
    Args:
        result (dict): The result dictionary
        session_id (str): The session ID
        
    Returns:
        dict: The updated result dictionary
    """
    # Create a hash from the session ID and command
    hash_input = f"{session_id}:{result['command']}"
    security_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    # Add the security hash to the watermark
    result['watermark'] = f"{result['watermark']} [Security: {security_hash}]"
    
    return result

def translate_to_command(natural_language, session_id):
    """
    Translate natural language to a Linux command.
    
    Args:
        natural_language (str): The natural language query
        session_id (str): Unique session identifier for security tracking
        
    Returns:
        dict: A dictionary containing the command, explanation, and watermark
    """
    # Generate the Linux command using OpenAI
    result = generate_linux_command(natural_language, session_id)
    
    # Add security checks
    if result['command'] and not is_safe_command(result['command']):
        result['command'] = "# Command not executed - potential security risk detected"
        result['explanation'] += "\n\nWARNING: This command was flagged as potentially unsafe."
    
    # Add a security hash to the result
    result = add_security_hash(result, session_id)
    
    return result

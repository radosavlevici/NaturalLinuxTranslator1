import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# List of potentially dangerous commands or patterns
DANGEROUS_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    ":(){:|:&};:",
    "dd if=/dev/random",
    "mv /* /dev/null",
    "wget .* | bash",
    "curl .* | bash",
    "> /dev/sda",
    "fork bomb",
    "char esp\\[\\]",  # Shellshock
]

# Commands that require extra caution
CAUTIOUS_COMMANDS = [
    "rm -rf",
    "dd",
    "mv",
    "chmod",
    "chown",
    "sudo",
    "su",
    "wget.*bash",
    "curl.*bash",
    "shutdown",
    "reboot",
    "halt",
    "init",
    "mkfs",
]

def validate_command(command):
    """
    Validates Linux commands for potentially dangerous operations
    
    Args:
        command (str): The Linux command to validate
        
    Returns:
        tuple: (is_safe, message) - Boolean indicating if command is safe and message explaining why if not
    """
    # Skip validation for empty commands or comment-only lines
    if not command or command.strip().startswith('#'):
        return True, "Empty command or comment"
    
    # Check for obviously dangerous commands
    for dangerous in DANGEROUS_COMMANDS:
        if re.search(dangerous, command, re.IGNORECASE):
            return False, f"Command contains dangerous pattern: {dangerous}"
    
    # Check for commands that need caution
    for cautious in CAUTIOUS_COMMANDS:
        if re.search(cautious, command, re.IGNORECASE):
            # We don't block these commands, but add a warning
            logging.warning(f"Command contains pattern that requires caution: {cautious}")
            return True, f"Use caution: command contains pattern '{cautious}' that could be dangerous if misused"
    
    # Command appears safe
    return True, "Command passed safety validation"

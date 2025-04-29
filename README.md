# Command Translator

A natural language to command translator tool that intelligently converts conversational English queries into precise terminal commands for both Linux and PowerShell environments.

## 🌟 Features

- **Natural Language Processing**: Translate plain English into exact commands
- **Multi-Platform Support**: Works with both Linux and PowerShell
- **Command Execution**: Execute translated commands directly (with safety checks)
- **Simple Interface**: Clean, user-friendly web interface
- **Comprehensive Explanations**: Each command comes with detailed explanations
- **Safety Checks**: Built-in validation to prevent dangerous command execution

## 📋 Requirements

- Python 3.6+
- Flask
- OpenAI API key (for GPT-4o model access)
- Internet connection (for API calls)

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YourUsername/command-translator.git
   cd command-translator
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key as an environment variable:
   ```bash
   # Linux/Mac
   export OPENAI_API_KEY="your-api-key-here"
   
   # Windows PowerShell
   $env:OPENAI_API_KEY="your-api-key-here"
   ```

4. Run the application:
   ```bash
   python main.py
   ```

5. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

## 🔒 Security Considerations

- The application has a built-in safety check for Linux commands
- Only a predefined set of safe commands will be executed
- PowerShell execution is simulated in this version (not executed directly)
- Always review commands before execution

## 🔄 PowerShell Integration

To integrate with PowerShell environments:

1. For full PowerShell execution, you'll need to modify the `execute()` function in `main.py`:
   ```python
   # Replace the PowerShell simulation section with:
   if mode == 'powershell':
       try:
           # Use subprocess to call PowerShell
           result = subprocess.run(
               ["powershell", "-Command", command],
               capture_output=True,
               text=True,
               timeout=5
           )
           output = result.stdout
           error = result.stderr
       except Exception as e:
           error = f"Error executing PowerShell command: {str(e)}"
   ```

2. For security, implement a similar safety check for PowerShell commands:
   ```python
   SAFE_POWERSHELL_COMMANDS = [
       'Get-ChildItem', 'Get-Location', 'Get-Content', 'Select-String',
       'Get-Process', 'Get-Date', 'Get-Service', 'Get-Command',
       # Add more safe commands as needed
   ]
   
   def is_safe_powershell_command(command):
       # Extract the main cmdlet name
       cmd_parts = command.strip().split()
       if not cmd_parts:
           return False
       main_cmd = cmd_parts[0]
       return main_cmd in SAFE_POWERSHELL_COMMANDS
   ```

## 🐧 Linux Integration

For deeper Linux integration:

1. To increase the allowed command set, modify the `SAFE_LINUX_COMMANDS` list in `main.py`:
   ```python
   SAFE_LINUX_COMMANDS = [
       'ls', 'pwd', 'cd', 'echo', 'cat', 'head', 'tail', 
       'grep', 'find', 'wc', 'date', 'cal', 'uname', 'whoami',
       # Add additional safe commands
   ]
   ```

2. For a system-wide installation, create a systemd service:
   ```
   [Unit]
   Description=Command Translator Service
   After=network.target

   [Service]
   User=youruser
   WorkingDirectory=/path/to/command-translator
   ExecStart=/usr/bin/python3 /path/to/command-translator/main.py
   Restart=always
   Environment=OPENAI_API_KEY=your-api-key-here

   [Install]
   WantedBy=multi-user.target
   ```

## 📜 License - 100% FREE OPEN SOURCE SOFTWARE - NO MONETIZATION ALLOWED WHATSOEVER

This project is COMPLETELY FREE and OPEN SOURCE under the GNU GPL v3 License with strict additional terms.

### ⚠️ ZERO TOLERANCE FOR MAKING MONEY FROM THIS SOFTWARE ⚠️
1. ⛔ NOBODY can sell this software - EVER - UNDER ANY CIRCUMSTANCES
2. ⛔ NOBODY can make money from this software in ANY WAY WHATSOEVER
3. ⛔ NOBODY can include this in ANY commercial/paid product or service
4. ⛔ NOBODY can charge for installation, support, or training for this software
5. ⛔ NOBODY can monetize through donations, advertising, or sponsorships
6. ⛔ NOBODY can require payment for any features or functionality
7. ⛔ ANY ATTEMPT to profit from this software in any form is STRICTLY PROHIBITED
8. ⛔ NO EXCEPTIONS will be made to these rules under any circumstances

### Open Source Freedom:
1. ✅ You CAN use this software for any personal or organizational purpose
2. ✅ You CAN distribute this software to others (for free only)
3. ✅ You CAN modify the source code (while maintaining copyright notices)
4. ✅ You CAN contribute improvements back to the project
5. ✅ You CAN create and share extensions or plugins (must also be free)

⚠️ IMPORTANT: This software is FREE OPEN SOURCE and should NEVER be sold. If anyone tries to charge you for this software, they are SCAMMERS. ⚠️

See LICENSE.md and FREE_SOFTWARE_NOTICE.md for complete details.

## 🧠 How It Works

The application uses OpenAI's GPT-4o model to:
1. Analyze the user's natural language query
2. Determine the appropriate command syntax
3. Generate the exact command to accomplish the requested task
4. Provide an explanation of how the command works

Commands are validated for safety before execution to prevent potentially dangerous operations.

## 👤 Author

Created by Ervin Remus Radosavlevici - Contact: ervin210@icloud.com | +447759313990

## 📄 OPEN SOURCE FREE SOFTWARE DECLARATION

This software is 100% FREE OPEN SOURCE. It is licensed under the GNU GPL v3 License, meaning:

- ✅ FREE to use for any non-commercial purpose
- ✅ FREE to study and learn from the source code
- ✅ FREE to modify and create your own versions
- ✅ FREE to distribute your modifications (as free software)
- ✅ PROTECTED by copyleft - derivatives must also be free and open source

⚠️ SCAM ALERT: This software should NEVER be sold. If anyone is charging money for this software, they are SCAMMERS. Please report any such activity to the author. ⚠️

### Why We Made This Free Open Source

This software was created to help everyone easily translate natural language to terminal commands. We believe in open access to tools that make technology more accessible. By making this completely free and open source, we ensure it remains available to all users regardless of their financial situation and encourage community contributions to make it even better.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4o API
- Contributors and testers who helped improve this tool
- Ervin Remus Radosavlevici for the original concept and design
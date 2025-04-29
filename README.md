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

## 📜 License

This project is licensed under [MIT License](LICENSE.md) for personal and open-source use. For commercial applications, please see our [Business License](BUSINESS_LICENSE.md) options.

## 🧠 How It Works

The application uses OpenAI's GPT-4o model to:
1. Analyze the user's natural language query
2. Determine the appropriate command syntax
3. Generate the exact command to accomplish the requested task
4. Provide an explanation of how the command works

Commands are validated for safety before execution to prevent potentially dangerous operations.

## 👤 Author

Created by Ervin Remus Radosavlevici - Contact: ervin210@icloud.com | +447759313990

## 📄 License Options

### MIT License (Recommended)

The MIT License is a permissive license that allows for reuse in both commercial and non-commercial projects with minimal restrictions, requiring only that the original copyright notice and license be included in any substantial copies of the software.

### Apache License 2.0

The Apache License 2.0 is another permissive license that also provides an express grant of patent rights from contributors to users.

### GNU General Public License (GPL)

The GPL is a copyleft license that requires any modified versions of the software to also be licensed under the GPL, ensuring that derivatives remain open source.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4o API
- Contributors and testers who helped improve this tool
- Ervin Remus Radosavlevici for the original concept and design
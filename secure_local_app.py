import os
from flask import Flask, request, jsonify, render_template_string

# Create Flask app with safer security but Replit-accessible
app = Flask(__name__)

# Simple HTML template
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Secure Command Translator</title>
    <style>
        body { background-color: #333; color: #fff; font-family: Arial; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        textarea, input { width: 100%; padding: 10px; margin: 10px 0; background: #444; color: #fff; border: 1px solid #555; }
        button { background: #555; color: #fff; padding: 10px 20px; border: none; cursor: pointer; }
        .result { background: #444; padding: 15px; margin-top: 20px; border-left: 4px solid #666; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Secure Command Translator</h1>
        <p>Running in Replit environment</p>
        
        <form id="translateForm" method="POST" action="/translate">
            <div>
                <label for="query">Enter your request:</label>
                <textarea id="query" name="query" rows="4" required>{{ query or '' }}</textarea>
            </div>
            
            <div>
                <label for="type">Command Type:</label>
                <select id="type" name="type">
                    <option value="linux" selected>Linux</option>
                    <option value="powershell">PowerShell</option>
                </select>
            </div>
            
            <button type="submit">Translate</button>
        </form>
        
        {% if command %}
        <div class="result">
            <h3>Command:</h3>
            <pre>{{ command }}</pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(TEMPLATE)

@app.route('/translate', methods=['POST'])
def translate():
    query = request.form.get('query', '')
    cmd_type = request.form.get('type', 'linux')
    
    if cmd_type == 'linux':
        command = f"Echo: This would translate your query: '{query}' to a Linux command"
    else:
        command = f"Echo: This would translate your query: '{query}' to a PowerShell command"
    
    return render_template_string(TEMPLATE, query=query, command=command)

@app.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.json
    query = data.get('query', '')
    cmd_type = data.get('type', 'linux')
    
    if cmd_type == 'linux':
        command = f"Echo: Linux command for: {query}"
    else:
        command = f"Echo: PowerShell command for: {query}"
    
    return jsonify({
        "command": command,
        "type": cmd_type
    })

if __name__ == '__main__':
    print("Starting Replit-accessible application...")
    print("Access via Replit webview")
    # Bind to 0.0.0.0 to make it accessible via Replit
    app.run(debug=True, host='0.0.0.0', port=5000)

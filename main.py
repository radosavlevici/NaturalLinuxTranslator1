from flask import Flask, render_template

# Create the Flask app
app = Flask(__name__)

# Simple home route
@app.route('/')
def index():
    """Render the static command reference page"""
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
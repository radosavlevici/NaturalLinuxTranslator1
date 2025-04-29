# Installation Guide

This document provides instructions for installing and running the Linux Command Translator application.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- A valid OpenAI API key

## Required Packages

The application requires the following Python packages:
- flask
- flask-sqlalchemy
- gunicorn
- openai
- email-validator
- psycopg2-binary

## Environment Setup

1. Clone the repository to your local machine:
   ```
   git clone <repository-url>
   cd linux-command-translator
   ```

2. Set up a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install flask flask-sqlalchemy gunicorn openai email-validator psycopg2-binary
   ```

4. Set up environment variables:
   ```
   # Linux/macOS
   export OPENAI_API_KEY="your-openai-api-key"
   export SESSION_SECRET="your-session-secret"

   # Windows
   set OPENAI_API_KEY=your-openai-api-key
   set SESSION_SECRET=your-session-secret
   ```

## Running the Application

1. Start the application using Gunicorn:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

2. Access the application in your web browser at:
   ```
   http://localhost:5000
   ```

## Notes

- Ensure your OpenAI API key has sufficient credits available
- For production deployment, consider using HTTPS
- Make sure all security settings are properly configured

## Troubleshooting

If you encounter any issues during installation or running the application:

1. Check that your environment variables are correctly set
2. Verify your OpenAI API key is valid
3. Check server logs for detailed error messages

---

© 2024 Ervin Remus Radosavlevici. All rights reserved.
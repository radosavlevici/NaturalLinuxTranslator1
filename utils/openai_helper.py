import os
import json
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def get_linux_command(query):
    """
    Convert natural language query to Linux command using OpenAI API
    
    Args:
        query (str): Natural language description of what the user wants to do
        
    Returns:
        dict: Contains the Linux command and explanation
    """
    try:
        # Define the system message
        system_message = """
        You are LinuxTranslator, an expert in Linux commands. Your task is to translate natural language 
        descriptions into appropriate Linux commands. Provide the command and a detailed explanation.
        
        For each translation:
        1. Focus on accurate command generation
        2. Provide detailed explanation of what the command does
        3. Include any safety warnings if applicable
        4. Format command options consistently
        
        Respond with JSON in the following format:
        {
            "command": "the linux command",
            "explanation": "detailed explanation of what the command does, each option, and any cautions"
        }
        """
        
        # Create user message with the query
        user_message = f"Translate this request into a Linux command: {query}"
        
        # Call the OpenAI API
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,  # Lower temperature for more deterministic results
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Ensure expected keys are present
        if "command" not in result or "explanation" not in result:
            raise ValueError("API response missing required fields")
            
        return result
        
    except Exception as e:
        logging.error(f"Error in OpenAI API call: {str(e)}")
        # Return a safe fallback
        return {
            "command": "# Error generating command",
            "explanation": f"Sorry, there was an error processing your request: {str(e)}"
        }

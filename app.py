from flask import Flask, render_template, request, session, redirect, jsonify
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
import traceback
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app and secret key
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
HF_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')

# Check and log API token existence (without revealing the actual token)
if not HF_API_TOKEN:
    logger.warning("HUGGINGFACE_API_TOKEN environment variable is not set!")

# Use Hugging Face Inference API with better error handling
def generate_text(prompt, max_new_tokens=100):
    API_URL = "https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    # Log API request (without sensitive information)
    logger.info(f"Sending request to Hugging Face API. Token exists: {bool(HF_API_TOKEN)}")
    
    # Format the prompt properly for chat models
    formatted_prompt = f"<human>: {prompt}\n<assistant>:"
    
    # Limit prompt size to avoid large payload errors
    if len(formatted_prompt) > 1000:
        formatted_prompt = formatted_prompt[:997] + "..."
    
    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.2,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        logger.info(f"API response status code: {response.status_code}")
        
        if response.status_code == 200:
            # Extract the generated text
            result = response.json()[0]["generated_text"]
            # Extract just the assistant's response
            assistant_response = result.split("<assistant>:")[-1].strip()
            return assistant_response
        else:
            # Log error details
            logger.error(f"API error: {response.status_code}, Response: {response.text[:200]}")
            return f"Sorry, I'm having trouble generating a response right now (Error {response.status_code}). Please try again with a shorter query."
    except Exception as e:
        # Handle any exceptions gracefully
        logger.error(f"Exception in generate_text: {str(e)}", exc_info=True)
        return f"I encountered an error: {str(e)}. Please try again with a shorter or different query."

# Make sure session data is properly initialized
@app.before_request
def before_request():
    try:
        # Initialize session if not exists
        if 'history' not in session:
            session['history'] = []
        if 'current_response' not in session:
            session['current_response'] = ""
    except Exception as e:
        logger.error(f"Error in before_request: {str(e)}", exc_info=True)
        # If session is completely broken, initialize empty values for this request
        session.clear()
        session['history'] = []
        session['current_response'] = ""

@app.route('/')
def home():
    try:
        # Safely get session data with defaults
        history = session.get('history', [])
        current_response = session.get('current_response', "")
        return render_template('index.html', history=history, current_response=current_response)
    except Exception as e:
        # Log and return error
        logger.error(f"Error in home route: {str(e)}", exc_info=True)
        return f"Error rendering template: {str(e)}", 500

@app.route('/generate', methods=['POST'])
def generate():
    try:
        prompt = request.form.get('prompt', '')
        
        if not prompt:
            logger.warning("Empty prompt received")
            return redirect('/')
        
        # Limit very long prompts
        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."
        
        # Generate text using the API with error handling
        generated_text = generate_text(prompt, max_new_tokens=150)
        
        # Safely update session
        history = session.get('history', [])
        history.append({
            'prompt': prompt,
            'response': generated_text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        session['history'] = history
        session['current_response'] = generated_text
        session.modified = True
        
    except Exception as e:
        # Log detailed error
        logger.error(f"Error in generate route: {str(e)}", exc_info=True)
        session['current_response'] = f"Sorry, I encountered an error processing your request: {str(e)}"
    
    return redirect('/')

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        session['history'] = []
        session['current_response'] = ""
        session.modified = True
    except Exception as e:
        logger.error(f"Error in clear_history: {str(e)}", exc_info=True)
        # If session fails, at least try to clear it
        session.clear()
    
    return redirect('/')

# Debug endpoint to check environment and session
@app.route('/debug', methods=['GET'])
def debug():
    try:
        return jsonify({
            "environment": {
                "FLASK_SECRET_KEY_EXISTS": bool(os.getenv('FLASK_SECRET_KEY')),
                "HF_API_TOKEN_EXISTS": bool(os.getenv('HUGGINGFACE_API_TOKEN')),
            },
            "session_available": bool(session),
            "session_keys": list(session.keys()) if session else []
        })
    except Exception as e:
        logger.error(f"Error in debug route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', 
                          history=session.get('history', []), 
                          current_response="Page not found. Please try again."), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {str(e)}", exc_info=True)
    return render_template('index.html', 
                          history=session.get('history', []), 
                          current_response="Server error occurred. Please try again later."), 500

# For Vercel serverless
app = app

# For local development
if __name__ == '__main__':
    app.run(debug=True)
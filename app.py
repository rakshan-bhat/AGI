from flask import Flask, render_template, request, session, redirect, jsonify
import os
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Hugging Face API settings
HF_API_TOKEN = os.environ.get('HUGGINGFACE_API_TOKEN')
HF_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

def generate_response(prompt, max_tokens=150):
    """Generate a response using the Hugging Face Inference API."""
    API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    # Format prompt for chat model
    formatted_prompt = f"<human>: {prompt}\n<assistant>:"
    
    # Limit prompt size
    if len(formatted_prompt) > 1000:
        formatted_prompt = formatted_prompt[:997] + "..."
    
    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()[0]["generated_text"]
            # Extract just the assistant's response
            assistant_response = result.split("<assistant>:")[-1].strip()
            return assistant_response
        else:
            logger.error(f"API error: {response.status_code}, {response.text[:200]}")
            return f"Sorry, I'm having trouble generating a response (Error {response.status_code})."
    except Exception as e:
        logger.error(f"Exception in generate_response: {str(e)}")
        return f"I encountered an error: {str(e)}. Please try again."

@app.route('/')
def home():
    """Render the home page with chat interface."""
    if 'history' not in session:
        session['history'] = []
    
    return render_template('index.html', 
                          history=session.get('history', []), 
                          current_response=session.get('current_response', ''))

@app.route('/generate', methods=['POST'])
def generate():
    """Handle chat form submission and generate response."""
    try:
        prompt = request.form.get('prompt', '').strip()
        
        if not prompt:
            return redirect('/')
        
        # Generate response
        response = generate_response(prompt)
        
        # Update session history
        history = session.get('history', [])
        history.append({
            'prompt': prompt,
            'response': response,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        session['history'] = history
        session['current_response'] = response
        session.modified = True
        
    except Exception as e:
        logger.error(f"Error in generate: {str(e)}")
        session['current_response'] = f"Error: {str(e)}"
    
    return redirect('/')

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear chat history."""
    session['history'] = []
    session['current_response'] = ""
    session.modified = True
    return redirect('/')

@app.route('/history')
def view_history():
    """View chat history page."""
    return render_template('history.html', history=session.get('history', []))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "ok", "model": HF_MODEL})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', 
                          history=session.get('history', []), 
                          current_response="Page not found. Please try again."), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('index.html', 
                          history=session.get('history', []), 
                          current_response="Server error occurred. Please try again later."), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
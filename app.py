from flask import Flask, render_template, request, session, redirect, jsonify
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
import traceback

# Load environment variables
load_dotenv()

# Initialize Flask app and secret key
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
HF_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')

# Use Hugging Face Inference API with better error handling
def generate_text(prompt, max_new_tokens=100):
    API_URL = "https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
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
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            # Extract the generated text
            result = response.json()[0]["generated_text"]
            # Extract just the assistant's response
            assistant_response = result.split("<assistant>:")[-1].strip()
            return assistant_response
        else:
            # Return a friendly error message instead of crashing
            return f"Sorry, I'm having trouble generating a response right now (Error {response.status_code}). Please try again with a shorter query."
    except Exception as e:
        # Handle any exceptions gracefully
        return f"I encountered an error: {str(e)}. Please try again with a shorter or different query."

@app.before_request
def before_request():
    if 'history' not in session:
        session['history'] = []
    if 'current_response' not in session:
        session['current_response'] = ""

@app.route('/')
def home():
    try:
        return render_template('index.html', history=session['history'], current_response=session['current_response'])
    except Exception as e:
        # Fallback in case of template errors
        return f"Error rendering template: {str(e)}"

@app.route('/generate', methods=['POST'])
def generate():
    try:
        prompt = request.form['prompt']
        
        # Limit very long prompts
        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."
        
        # Generate text using the API with error handling
        generated_text = generate_text(prompt, max_new_tokens=150)
        
        # Store current response
        session['current_response'] = generated_text
        
        # Store prompt and response in session history
        session['history'].append({
            'prompt': prompt,
            'response': generated_text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        session.modified = True
    except Exception as e:
        # Create a detailed error response without crashing
        error_detail = traceback.format_exc()
        session['current_response'] = f"Sorry, I encountered an error processing your request: {str(e)}"
    
    return redirect('/')

@app.route('/clear_history', methods=['POST'])
def clear_history():
    session['history'] = []
    session['current_response'] = ""
    session.modified = True
    return redirect('/')

# For Vercel serverless
app = app

# For local development
if __name__ == '__main__':
    app.run(debug=True)
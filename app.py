from flask import Flask, render_template, request, session, redirect, jsonify, url_for
from dotenv import load_dotenv
import os
from datetime import datetime
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app and secret key
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
HF_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')

# Use Hugging Face Inference API with error handling
def generate_text(prompt, max_new_tokens=100):
    API_URL = "https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    # Format the prompt properly for chat models
    formatted_prompt = f"<human>: {prompt}\n<assistant>:"
    
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
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            # Extract the generated text
            result = response.json()[0]["generated_text"]
            # Extract just the assistant's response
            assistant_response = result.split("<assistant>:")[-1].strip()
            return {"status": "success", "response": assistant_response}
        else:
            # Fallback for API errors
            return {
                "status": "error", 
                "response": "I'm currently experiencing difficulties with my AI service. Please try again in a moment."
            }
    except Exception as e:
        # Fallback for connection errors
        return {
            "status": "error",
            "response": "I'm temporarily unable to process your request. Let's try again shortly."
        }

@app.before_request
def before_request():
    if 'history' not in session:
        session['history'] = []
    if 'current_response' not in session:
        session['current_response'] = ""

@app.route('/')
def home():
    return render_template('index.html', 
                           history=session.get('history', []), 
                           current_response=session.get('current_response', ""))

@app.route('/history')
def history():
    return render_template('history.html', 
                           history=session.get('history', []))

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.form.get('prompt', '')
    
    if not prompt:
        return redirect(url_for('home'))
    
    try:
        # Generate text using the API
        result = generate_text(prompt, max_new_tokens=150)
        
        # Get the response
        generated_text = result["response"]
        
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
        # Fallback for any other errors
        session['current_response'] = "Sorry, I encountered an error processing your request."
    
    return redirect(url_for('home'))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    session['history'] = []
    session['current_response'] = ""
    session.modified = True
    return redirect(url_for('home'))

# For Vercel serverless
app = app

# For local development
if __name__ == '__main__':
    app.run(debug=True)
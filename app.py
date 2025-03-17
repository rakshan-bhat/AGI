from flask import Flask, render_template, request, session, redirect, jsonify, url_for
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
import json

# Load environment variables
load_dotenv()

# Initialize Flask app with explicit template and static folders
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Configure session - important for serverless
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secure-key-for-development')

# Simple in-memory fallback for serverless environments where session might not work
chat_history = []
current_chat_response = ""

# Use Hugging Face Inference API with error handling
def generate_text(prompt, max_new_tokens=100):
    try:
        # Serverless debug: log the environment state
        print(f"Generating text with prompt: {prompt[:20]}...")
        
        # For now, create a simple fallback that will always work
        # This helps us test if the rest of the app functions properly
        return {
            "status": "success",
            "response": f"Thank you for your message: '{prompt}'. This is a fallback response while we troubleshoot the API connection."
        }
        
        # The real implementation (commented out until we confirm the app works)
        """
        API_URL = "https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        headers = {"Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_TOKEN', '')}"}
        
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
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()[0]["generated_text"]
            assistant_response = result.split("<assistant>:")[-1].strip()
            return {"status": "success", "response": assistant_response}
        else:
            return {
                "status": "error", 
                "response": f"I'm currently experiencing difficulties with my AI service. Please try again in a moment."
            }
        """
    except Exception as e:
        print(f"Error generating text: {str(e)}")
        return {
            "status": "error",
            "response": "I'm temporarily unable to process your request. Let's try again shortly."
        }

# Safe way to access session variables with fallbacks
def get_history():
    try:
        if 'history' in session:
            return session['history']
        return chat_history
    except:
        return chat_history

def get_current_response():
    try:
        if 'current_response' in session:
            return session['current_response']
        return current_chat_response
    except:
        return current_chat_response

def set_history(history_data):
    global chat_history
    try:
        session['history'] = history_data
        session.modified = True
    except:
        chat_history = history_data

def set_current_response(response_text):
    global current_chat_response
    try:
        session['current_response'] = response_text
        session.modified = True
    except:
        current_chat_response = response_text

@app.route('/')
def home():
    try:
        # Try to render template with history from session or fallback
        history = get_history()
        current = get_current_response()
        return render_template('index.html', history=history, current_response=current)
    except Exception as e:
        # If template rendering fails, return a simple response
        print(f"Error rendering home template: {str(e)}")
        return f"Flask app is running. Template error: {str(e)}"

@app.route('/history')
def history():
    try:
        return render_template('history.html', history=get_history())
    except Exception as e:
        print(f"Error rendering history template: {str(e)}")
        return f"History page. Template error: {str(e)}"

@app.route('/generate', methods=['POST'])
def generate():
    try:
        prompt = request.form.get('prompt', '')
        
        if not prompt:
            return redirect('/')
        
        # Generate text using the simplified fallback
        result = generate_text(prompt, max_new_tokens=150)
        generated_text = result["response"]
        
        # Update history using our safe methods
        history = get_history()
        history.append({
            'prompt': prompt,
            'response': generated_text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Update session and fallbacks
        set_history(history)
        set_current_response(generated_text)
        
        return redirect('/')
    except Exception as e:
        print(f"Error in generate route: {str(e)}")
        return f"Error processing request: {str(e)}"

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        set_history([])
        set_current_response("")
        return redirect('/')
    except Exception as e:
        print(f"Error clearing history: {str(e)}")
        return f"Error clearing history: {str(e)}"

@app.route('/debug')
def debug():
    """Endpoint to help diagnose issues"""
    debug_info = {
        "env_vars": {k: "✓" for k in os.environ if not k.startswith("AWS_") and not k.startswith("VERCEL_")},
        "template_folder_exists": os.path.isdir(app.template_folder) if app.template_folder else False,
        "static_folder_exists": os.path.isdir(app.static_folder) if app.static_folder else False,
        "templates": os.listdir(app.template_folder) if app.template_folder and os.path.isdir(app.template_folder) else [],
        "session_working": "history" in session,
    }
    return jsonify(debug_info)

# For Vercel serverless
app = app

# For local development
if __name__ == '__main__':
    app.run(debug=True)
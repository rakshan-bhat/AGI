from flask import Flask, render_template, request, session, redirect
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv
import os
from datetime import datetime
import torch

# Load environment variables
load_dotenv()

# Initialize Flask app and secret key
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

# Initialize model with better parameters
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
# Check if GPU is available, but don't use device_map
if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    torch_dtype=torch.float16  # Use float16 for better performance
)
model = model.to(device)

# Create a custom pipeline with better settings
def generate_text(prompt, max_new_tokens=100):
    # Format the prompt properly for chat models
    formatted_prompt = f"<human>: {prompt}\n<assistant>:"
    
    # Generate with better parameters
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        inputs.input_ids,
        max_new_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.9,
        top_k=50,
        repetition_penalty=1.2,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    
    # Decode the response and remove the prompt
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    assistant_response = full_response.split("<assistant>:")[-1].strip()
    
    return assistant_response

@app.before_request
def before_request():
    if 'history' not in session:
        session['history'] = []
    if 'current_response' not in session:
        session['current_response'] = ""

@app.route('/')
def home():
    return render_template('index.html', history=session['history'], current_response=session['current_response'])

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.form['prompt']
    
    try:
        # Generate text using the improved function
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
        session['current_response'] = f"Error: {str(e)}"
    
    return redirect('/')

@app.route('/clear_history', methods=['POST'])
def clear_history():
    session['history'] = []
    session['current_response'] = ""
    session.modified = True
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
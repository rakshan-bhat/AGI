from flask import Flask, render_template, request, session
from transformers import pipeline
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Initialize GPT-2 pipeline
generator = pipeline('text-generation', model='gpt2')

# Initialize history storage
if 'history' not in session:
    session['history'] = []

@app.route('/')
def home():
    return render_template('index.html', history=session['history'])

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.form['prompt']
    response = generator(prompt, max_length=50, num_return_sequences=1)[0]['generated_text']
    
    # Store with timestamp
    session['history'].append({
        'prompt': prompt,
        'response': response,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    session.modified = True
    
    return redirect('/')

@app.route('/history')
def show_history():
    return render_template('history.html', history=session['history'])


if __name__ == '__main__':
    app.run(debug=True)

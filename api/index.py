from http.server import BaseHTTPRequestHandler
from urllib import parse
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        s = self.path
        parsed_path = parse.urlparse(s)
        path = parsed_path.path
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Simple AI Assistant</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    h1 { text-align: center; }
                    .chat-box { border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .form-container { background: #f9f9f9; padding: 20px; border-radius: 8px; }
                    input[type="text"] { width: 80%; padding: 10px; }
                    button { padding: 10px 20px; background: #4285f4; color: white; border: none; cursor: pointer; }
                </style>
            </head>
            <body>
                <h1>Simple AI Assistant</h1>
                <div class="chat-box">
                    <p>Hello! I'm a simple AI assistant. Ask me something!</p>
                </div>
                <div class="form-container">
                    <form action="/api" method="post">
                        <input type="text" name="prompt" placeholder="Ask me something...">
                        <button type="submit">Send</button>
                    </form>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
            return
        
        self.send_response(404)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(f"Not found: {path}".encode())
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Parse the form data
        data = parse.parse_qs(post_data.decode('utf-8'))
        prompt = data.get('prompt', [''])[0]
        
        # Generate a simple response
        response = f"You said: {prompt}"
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Simple AI Assistant</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ text-align: center; }}
                .chat-box {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .form-container {{ background: #f9f9f9; padding: 20px; border-radius: 8px; }}
                input[type="text"] {{ width: 80%; padding: 10px; }}
                button {{ padding: 10px 20px; background: #4285f4; color: white; border: none; cursor: pointer; }}
                .user-message {{ background: #e6f7ff; padding: 10px; border-radius: 8px; margin-bottom: 10px; }}
                .ai-message {{ background: #f1f1f1; padding: 10px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <h1>Simple AI Assistant</h1>
            <div class="chat-box">
                <div class="user-message">
                    <strong>You:</strong> {prompt}
                </div>
                <div class="ai-message">
                    <strong>Assistant:</strong> {response}
                </div>
            </div>
            <div class="form-container">
                <form action="/api" method="post">
                    <input type="text" name="prompt" placeholder="Ask me something...">
                    <button type="submit">Send</button>
                </form>
            </div>
            <p><a href="/">Start New Conversation</a></p>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
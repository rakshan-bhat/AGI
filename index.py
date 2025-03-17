# Monkey patch Werkzeug before importing Flask
import werkzeug
if not hasattr(werkzeug.urls, 'url_quote'):
    werkzeug.urls.url_quote = werkzeug.urls.quote if hasattr(werkzeug.urls, 'quote') else lambda x: x

# Now import the app
try:
    from app import app
except ImportError as e:
    # Create a minimal Flask app for error reporting
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return jsonify({
            "error": "Application failed to start",
            "details": str(e),
            "werkzeug_patched": hasattr(werkzeug.urls, 'url_quote')
        }), 500

# Need this for Vercel
app = app
from flask import Flask, Response
import os

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return Response("Flask API is working!", mimetype="text/plain")

# This handler is necessary for Vercel
def handler(request, context):
    return app(request, context)
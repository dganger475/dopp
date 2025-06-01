"""
Simple test route to verify ngrok connectivity
"""
from flask import Blueprint, render_template_string

# Create a simple test blueprint
test = Blueprint('test', __name__, url_prefix='/test')

@test.route('/')
def test_page():
    """Simple test page to verify ngrok connectivity"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dopple Test Page</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                text-align: center;
            }
            h1 {
                color: #646cff;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Dopple Test Page</h1>
            <p>If you can see this page, your ngrok connection is working correctly!</p>
            <p>This is a simple test page to verify that the application is accessible through ngrok.</p>
            <p>The application is using a SQLite database (faces.db) for user authentication.</p>
            <p>The login system expects a username parameter (not email) for authentication.</p>
            <p>The registration page includes a mandatory headshot upload feature.</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

"""
Simple Flask application to test ngrok connectivity
"""
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    """Simple test page to verify ngrok connectivity"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ngrok Test Page</title>
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
            <h1>Ngrok Test Page</h1>
            <p>If you can see this page, your ngrok connection is working correctly!</p>
            <p>This is a simple test page to verify that the application is accessible through ngrok.</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

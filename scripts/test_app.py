from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    print("Route accessed!")  # This will show in the console
    return "Hello, World!"

if __name__ == '__main__':
    print("Starting Flask app...")  # This should show when you start the app
    app.run(debug=True, port=5000)
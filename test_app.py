from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://localhost:3000"], "supports_credentials": True}})

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        "success": True,
        "message": "API is working",
        "data": {
            "user": {
                "id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "image": "/static/images/profiles/test.jpg",
                "coverPhoto": "/static/images/covers/test.jpg",
                "bio": "This is a test user",
                "currentCity": "Test City",
                "state": "TS",
                "hometown": "Test Town",
                "memberSince": "2025-01-01",
                "fullName": "Test User"
            }
        }
    })

if __name__ == '__main__':
    app.run(debug=True)

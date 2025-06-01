"""
Test script to verify beta testing setup for DoppleGanger application
"""
import os
import requests
import webbrowser
import time
import socket
import json
from urllib.parse import urljoin

def check_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_local_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def test_flask_server():
    """Test if the Flask server is running and accessible."""
    try:
        response = requests.get('http://localhost:5000/auth/login', timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is running and accessible at http://localhost:5000")
            return True
        else:
            print(f"❌ Flask server returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Flask server is not accessible: {e}")
        return False

def test_cors_headers():
    """Test if the CORS headers are properly set."""
    try:
        response = requests.options('http://localhost:5000/auth/login', 
                                   headers={'Origin': 'http://example.com'}, 
                                   timeout=5)
        
        if 'Access-Control-Allow-Origin' in response.headers:
            origin = response.headers['Access-Control-Allow-Origin']
            if origin == '*' or origin == 'http://example.com':
                print(f"✅ CORS headers are properly set: Access-Control-Allow-Origin={origin}")
                return True
            else:
                print(f"❌ CORS headers are not properly set: Access-Control-Allow-Origin={origin}")
                return False
        else:
            print("❌ CORS headers are missing")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_beta_setup():
    """Test the beta testing setup."""
    print("\n=== DoppleGanger Beta Testing Setup Check ===\n")
    
    # Check if Flask server is running
    flask_running = test_flask_server()
    
    if not flask_running:
        print("\n❌ Flask server is not running. Please start it with 'python run.py'")
        return False
    
    # Test CORS headers
    cors_working = test_cors_headers()
    
    if not cors_working:
        print("\n❌ CORS headers are not properly set. Check your CORS middleware configuration.")
        return False
    
    # Get local IP for LAN testing
    local_ip = get_local_ip()
    
    print("\n=== Beta Testing Setup Results ===\n")
    print(f"✅ Your application is running and accessible at:")
    print(f"   - Local: http://localhost:5000")
    print(f"   - LAN: http://{local_ip}:5000 (share this with testers on your local network)")
    print("\nReminder: Your application uses:")
    print("   - SQLite database (faces.db) for user data")
    print("   - Username-based authentication (not email)")
    print("   - Mandatory headshot upload during registration")
    
    print("\nTo test the application:")
    print("1. Register with a username, email, password, and upload a headshot photo")
    print("2. The headshot photo will be processed to extract face encodings")
    print("3. Log in with your username and password")
    print("4. Test the profile page and other features")
    
    return True

if __name__ == "__main__":
    test_beta_setup()

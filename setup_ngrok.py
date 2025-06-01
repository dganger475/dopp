"""
Setup ngrok for beta testing with proper configuration
"""
import os
import sys
import subprocess
import time
import requests
import json
import webbrowser
from urllib.parse import urlparse

def check_ngrok_running():
    """Check if ngrok is already running by trying to access the API"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            return True
        return False
    except:
        return False

def get_ngrok_tunnels():
    """Get the current ngrok tunnels"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            return response.json()["tunnels"]
        return []
    except:
        return []

def kill_ngrok_processes():
    """Kill all ngrok processes"""
    try:
        if sys.platform == "win32":
            os.system("taskkill /F /IM ngrok.exe")
        else:
            os.system("pkill -f ngrok")
        print("✅ Killed existing ngrok processes")
        time.sleep(1)
    except:
        pass

def setup_ngrok():
    """Set up ngrok for beta testing"""
    print("\n=== Setting up ngrok for beta testing ===\n")
    
    # Check if ngrok is already running
    if check_ngrok_running():
        print("⚠️ ngrok is already running. Checking existing tunnels...")
        tunnels = get_ngrok_tunnels()
        if tunnels:
            for tunnel in tunnels:
                public_url = tunnel.get("public_url", "")
                if public_url:
                    print(f"✅ Existing ngrok tunnel found: {public_url}")
                    return public_url
        
        print("⚠️ Existing ngrok process found but no valid tunnels. Restarting ngrok...")
        kill_ngrok_processes()
    
    # Start ngrok with the right configuration
    try:
        # Use a simpler ngrok configuration
        cmd = ["ngrok", "http", "--region=us", "--host-header=rewrite", "5000"]
        
        # Start ngrok in the background
        if sys.platform == "win32":
            process = subprocess.Popen(cmd, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            process = subprocess.Popen(cmd, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
        
        print("✅ Started ngrok process")
        
        # Wait for ngrok to start up
        max_attempts = 10
        attempts = 0
        tunnel_url = None
        
        while attempts < max_attempts:
            time.sleep(2)  # Give ngrok time to start
            attempts += 1
            print(f"⏳ Waiting for ngrok to start... (attempt {attempts}/{max_attempts})")
            
            try:
                tunnels = get_ngrok_tunnels()
                if tunnels:
                    for tunnel in tunnels:
                        public_url = tunnel.get("public_url", "")
                        if public_url:
                            tunnel_url = public_url
                            break
                    
                    if tunnel_url:
                        break
            except:
                pass
        
        if tunnel_url:
            print(f"\n✅ ngrok tunnel established successfully!")
            print(f"\n=== Beta Testing Information ===")
            print(f"\nShare this URL with your beta testers: {tunnel_url}")
            print("\nReminder: Your application uses:")
            print("   - SQLite database (faces.db) for user data")
            print("   - Username-based authentication (not email)")
            print("   - Mandatory headshot upload during registration")
            
            # Try to open the ngrok web interface
            try:
                webbrowser.open("http://localhost:4040")
                print("\n✅ Opened ngrok web interface in your browser")
            except:
                print("\n⚠️ Could not open ngrok web interface. You can access it at: http://localhost:4040")
            
            return tunnel_url
        else:
            print("\n❌ Failed to establish ngrok tunnel after multiple attempts")
            return None
    
    except Exception as e:
        print(f"\n❌ Error setting up ngrok: {str(e)}")
        return None

if __name__ == "__main__":
    setup_ngrok()

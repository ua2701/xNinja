from flask import Flask, jsonify
import asyncio
import yaml
from login_script_2 import login_and_keep_open  # Import the modified login function

app = Flask(__name__)

def load_config():
    """Load configuration from YAML file"""
    with open('login.yaml', 'r') as file:
        return yaml.safe_load(file)

@app.route('/username', methods=['GET'])
def trigger_login():
    try:
        config = load_config()
        # Run the login in a separate thread to avoid blocking Flask
        import threading
        thread = threading.Thread(target=lambda: asyncio.run(login_and_keep_open(config)))
        thread.daemon = True  # Dies when main thread dies
        thread.start()
        
        return jsonify({"message": "Login automation started. Browser will remain open for user interaction."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
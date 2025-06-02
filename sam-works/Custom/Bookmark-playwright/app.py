from flask import Flask, jsonify
import asyncio
import yaml
from login_script import login  # Import the login function instead of main

app = Flask(__name__)

def load_config():
    """Load configuration from YAML file"""
    with open('login.yaml', 'r') as file:
        return yaml.safe_load(file)

@app.route('/username', methods=['GET'])
def trigger_login():
    try:
        config = load_config()
        asyncio.run(login(config))  # Call login function with config
        return jsonify({"message": "Login automation completed."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
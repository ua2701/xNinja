from flask import Flask, jsonify
import asyncio
import yaml
import threading
from login_script_3 import login_and_keep_open  # Import the modified login function

app = Flask(__name__)

# Global variable to keep track of browser instances
active_browsers = []

def load_config():
    """Load configuration from YAML file"""
    with open('login.yaml', 'r') as file:
        return yaml.safe_load(file)

def run_login_async(config):
    """Wrapper function to run async login in a separate thread"""
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(login_and_keep_open(config, active_browsers))
    except Exception as e:
        print(f"Error in login thread: {e}")

@app.route('/username', methods=['GET'])
def trigger_login():
    try:
        config = load_config()
        # Run the login in a separate thread with its own event loop
        thread = threading.Thread(target=run_login_async, args=(config,))
        thread.daemon = False  # Keep thread alive to maintain browser
        thread.start()
        
        return jsonify({"message": "Login automation started. Browser will remain open for user interaction."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/close-browsers', methods=['POST'])
def close_all_browsers():
    """Optional endpoint to close all active browsers"""
    global active_browsers
    closed_count = 0
    for browser in active_browsers:
        try:
            asyncio.run(browser.close())
            closed_count += 1
        except:
            pass
    active_browsers.clear()
    return jsonify({"message": f"Closed {closed_count} browser instances."})

if __name__ == '__main__':
    app.run(port=5000)
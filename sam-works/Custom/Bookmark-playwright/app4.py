from flask import Flask, jsonify, request
import asyncio
import yaml
import threading
from login_script_4 import login_and_keep_open, get_app_config, load_config

app = Flask(__name__)

# Global variable to keep track of browser instances
active_browsers = []

def run_login_async(app_config):
    """Wrapper function to run async login in a separate thread"""
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(login_and_keep_open(app_config, active_browsers))
    except Exception as e:
        print(f"Error in login thread: {e}")

@app.route('/<app_name>/<username>', methods=['GET'])
def trigger_login(app_name, username):
    """Trigger login for a specific application"""
    try:
        app_config = get_app_config(app_name)
        
        # Override username if provided in URL
        if username and username != '<username>':
            app_config["login"]["username"] = username
        
        # Run the login in a separate thread with its own event loop
        thread = threading.Thread(target=run_login_async, args=(app_config,))
        thread.daemon = False  # Keep thread alive to maintain browser
        thread.start()
        
        return jsonify({
            "message": f"Login automation started for {app_name}",
            "application": app_name,
            "username": app_config["login"]["username"],
            "url": app_config["login"]["url"],
            "note": "Browser will remain open for user interaction."
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/applications', methods=['GET'])
def list_applications():
    """List all available applications"""
    try:
        config = load_config()
        apps = {}
        for app_name, app_config in config["applications"].items():
            apps[app_name] = {
                "code_url": app_config["code_url"],
                "login_url": app_config["login"]["url"],
                "username": app_config["login"]["username"]
            }
        return jsonify({"applications": apps})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/applications/<app_name>', methods=['GET'])
def get_application_info(app_name):
    """Get information about a specific application"""
    try:
        app_config = get_app_config(app_name)
        return jsonify({
            "application": app_name,
            "code_url": app_config["code_url"],
            "login_url": app_config["login"]["url"],
            "username": app_config["login"]["username"],
            "selectors": {
                "username": app_config["login"]["username_selector"],
                "password": app_config["login"]["password_selector"],
                "login_button": app_config["login"].get("login_button_selector", 
                    f"role: {app_config['login'].get('login_button_role')} name: {app_config['login'].get('login_button_name')}")
            }
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login_with_payload():
    """Start login using JSON payload"""
    try:
        data = request.get_json()
        app_name = data.get('app_name')
        username = data.get('username')
        password = data.get('password')
        
        if not app_name:
            return jsonify({"error": "app_name is required"}), 400
            
        app_config = get_app_config(app_name)
        
        # Override credentials if provided
        if username:
            app_config["login"]["username"] = username
        if password:
            app_config["login"]["password"] = password
        
        # Run the login in a separate thread
        thread = threading.Thread(target=run_login_async, args=(app_config,))
        thread.daemon = False
        thread.start()
        
        return jsonify({
            "message": f"Login automation started for {app_name}",
            "application": app_name,
            "username": app_config["login"]["username"]
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current status of active browsers"""
    return jsonify({
        "active_browsers": len(active_browsers),
        "message": f"{len(active_browsers)} browser instances currently active"
    })

@app.route('/close-browsers', methods=['POST'])
def close_all_browsers():
    """Close all active browsers"""
    global active_browsers
    closed_count = 0
    for browser in active_browsers:
        try:
            # Create a new event loop to close the browser
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(browser.close())
            closed_count += 1
        except:
            pass
    active_browsers.clear()
    return jsonify({"message": f"Closed {closed_count} browser instances."})

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        "message": "Multi-Application Login Automation API",
        "endpoints": {
            "GET /": "This help message",
            "GET /applications": "List all available applications",
            "GET /applications/<app_name>": "Get information about a specific application",
            "GET /<app_name>/<username>": "Start login for application with username",
            "POST /login": "Start login with JSON payload {app_name, username, password}",
            "GET /status": "Get current status",
            "POST /close-browsers": "Close all active browsers"
        },
        "example_urls": [
            "GET /magento/john.doe@example.com",
            "GET /parabank/testuser",
            "POST /login with {\"app_name\": \"saucedemo\", \"username\": \"standard_user\"}"
        ]
    })

if __name__ == '__main__':
    print("Starting Multi-Application Login Automation Server...")
    print("Available endpoints:")
    print("  GET  /applications - List all applications")
    print("  GET  /<app_name>/<username> - Start login")
    print("  POST /login - Login with JSON payload")
    print("  GET  /status - Check browser status")
    print("  POST /close-browsers - Close all browsers")
    app.run(host='0.0.0.0', port=5000, debug=True)
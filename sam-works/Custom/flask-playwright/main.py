from flask import Flask, abort, request, jsonify
import subprocess
import urllib.parse
import threading
import time
import json
import os

app = Flask(__name__)

# Hardcoded valid username
VALID_USERNAME = "hello.world@gmail.com"

def run_playwright_script(username, okta_url=None, mode="auto"):
    """Run the playwright script with optional Okta URL"""
    try:
        cmd = ["python", "playwright_script.py", username, mode]
        if okta_url:
            cmd.append(okta_url)
        
        print(f"[INFO] Running command: {' '.join(cmd)}")
        
        # Run in background thread to avoid blocking Flask
        result = subprocess.run(cmd, 
                              check=True, 
                              capture_output=True, 
                              text=True,
                              timeout=120)  # 2 minute timeout
        
        print(f"[SUCCESS] Playwright script output: {result.stdout}")
        if result.stderr:
            print(f"[WARNING] Playwright script stderr: {result.stderr}")
        
        return True, result.stdout
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Playwright script failed with exit code {e.returncode}"
        if e.stdout:
            error_msg += f"\nStdout: {e.stdout}"
        if e.stderr:
            error_msg += f"\nStderr: {e.stderr}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    except subprocess.TimeoutExpired as e:
        error_msg = "Playwright script timed out after 2 minutes"
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg

@app.route('/BankOfGuam/<path:username>', methods=['GET'])
@app.route('/Entrust/<path:username>', methods=['GET'])
def handle_login(username):
    """Handle login requests from Okta bookmark or direct URL"""
    # Decode any URL-encoded characters (e.g., %40 -> @)
    decoded_username = urllib.parse.unquote(username)
    
    # Get optional Okta URL from query parameters
    okta_url = request.args.get('okta_url')
    mode = request.args.get('mode', 'auto')  # Default to auto mode
    
    print(f"[INFO] Received request for username: {decoded_username}")
    if okta_url:
        print(f"[INFO] Okta URL provided: {okta_url}")
    
    if decoded_username != VALID_USERNAME:
        print("[WARNING] Unauthorized username attempted.")
        abort(403, description="Unauthorized username")

    print("[INFO] Username authorized. Launching Playwright script...")
    
    # Run script asynchronously to avoid blocking
    def run_script_async():
        success, output = run_playwright_script(decoded_username, okta_url, mode)
        if success:
            print(f"[SUCCESS] Script completed for {decoded_username}")
        else:
            print(f"[ERROR] Script failed for {decoded_username}: {output}")
    
    # Start script in background thread
    script_thread = threading.Thread(target=run_script_async)
    script_thread.daemon = True
    script_thread.start()
    
    response_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bank of Guam SSO Login</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .success {{ color: #27ae60; text-align: center; }}
            .info {{ color: #3498db; margin-top: 20px; }}
            .note {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="success">✅ Login Process Started</h1>
            <p class="success">Script successfully triggered for <strong>{decoded_username}</strong></p>
            
            <div class="info">
                <h3>What's happening:</h3>
                <ul>
                    <li>Browser window will open automatically</li>
                    <li>Login process will complete in the background</li>
                    <li>Browser session will remain active after login</li>
                    <li>You can close this tab</li>
                </ul>
            </div>
            
            {f'<div class="note"><strong>Okta URL:</strong> {okta_url}</div>' if okta_url else ''}
            
            <div class="note">
                <strong>Note:</strong> The browser session will stay open for SSO purposes. 
                Manually close the browser when you're done.
            </div>
        </div>
    </body>
    </html>
    """
    
    return response_html, 200

@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "valid_username": VALID_USERNAME,
        "endpoints": [
            "/BankOfGuam/<username>",
            "/Entrust/<username>"
        ]
    })

@app.route('/', methods=['GET'])
def home():
    """Home page with usage instructions"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bank of Guam SSO Service</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
            .endpoint {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 10px 0; }}
            .code {{ background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏦 Bank of Guam SSO Service</h1>
                <p>Automated login service with Okta integration</p>
            </div>
            
            <h2>Available Endpoints:</h2>
            
            <div class="endpoint">
                <h3>Direct Login</h3>
                <div class="code">GET /BankOfGuam/{VALID_USERNAME}</div>
                <div class="code">GET /Entrust/{VALID_USERNAME}</div>
            </div>
            
            <div class="endpoint">
                <h3>With Okta URL</h3>
                <div class="code">GET /BankOfGuam/{VALID_USERNAME}?okta_url=https://your-org.okta.com/app/...</div>
            </div>
            
            <div class="endpoint">
                <h3>Interactive Mode</h3>
                <div class="code">GET /BankOfGuam/{VALID_USERNAME}?mode=interactive</div>
            </div>
            
            <h2>Features:</h2>
            <ul>
                <li>✅ Automated login process</li>
                <li>✅ Okta bookmark support</li>
                <li>✅ Session persistence (browser stays open)</li>
                <li>✅ Auto-detach mode (script exits, browser remains)</li>
                <li>✅ Screenshot and session export</li>
            </ul>
            
            <h2>Status:</h2>
            <p>Service is running on port 5000</p>
            <p>Valid username: <strong>{VALID_USERNAME}</strong></p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("[INFO] Starting Bank of Guam SSO Flask Application...")
    print(f"[INFO] Valid username: {VALID_USERNAME}")
    print("[INFO] Available endpoints:")
    print(f"  - GET /BankOfGuam/{VALID_USERNAME}")
    print(f"  - GET /Entrust/{VALID_USERNAME}")
    print("[INFO] Optional query parameters:")
    print("  - okta_url: Okta bookmark URL")
    print("  - mode: 'auto' (default) or 'interactive'")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
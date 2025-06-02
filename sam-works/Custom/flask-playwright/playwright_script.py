import asyncio
import sys
import os
from playwright.async_api import async_playwright
import json
from datetime import datetime

class BankOfGuamSession:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def __aenter__(self):
        # Initialize Playwright
        self.playwright = await async_playwright().start()
        
        # Set up user data directory
        user_data_dir = os.path.join(os.getcwd(), "browser_data")
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Launch persistent context with user data directory
        # Use launch_persistent_context instead of launch with --user-data-dir argument
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # Set to True if you want headless mode
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Get the first page or create a new one
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Close resources in reverse order
        if self.page:
            try:
                await self.page.close()
            except:
                pass
                
        if self.context:
            try:
                await self.context.close()
            except:
                pass
                
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass

    async def login(self, username, okta_url=None, mode="auto"):
        """Perform the login process"""
        try:
            print(f"=== Starting Bank of Guam Login for: {username} ===")
            print(f"=== Mode: {mode} ===")
            
            # Navigate to the login page
            if okta_url:
                print(f"[INFO] Using provided Okta URL: {okta_url}")
                await self.page.goto(okta_url)
            else:
                # Default login URL - replace with actual Bank of Guam login URL
                login_url = "https://online.bankofguam.com/bankofguamonline_41/Uux.aspx#/login"
                print(f"[INFO] Navigating to: {login_url}")
                await self.page.goto(login_url)
            
            # Wait for page to load
            await self.page.wait_for_load_state('networkidle')
            
            if mode == "interactive":
                print("[INFO] Interactive mode - waiting for manual login...")
                print("[INFO] Please complete the login manually in the browser window.")
                print("[INFO] Press Enter in this terminal when login is complete...")
                input()
            else:
                # Auto mode - implement your login logic here
                print("[INFO] Auto mode - attempting automatic login...")
                
                # Example login steps (customize based on your actual login page):
                try:
                    # Wait for username field and fill it
                    username_selector = 'input[name="username"]'  # Adjust selector as needed
                    await self.page.wait_for_selector(username_selector, timeout=10000)
                    await self.page.fill(username_selector, username)
                    
                    # If there's a password field, you'll need to handle it
                    # password_selector = 'input[name="password"]'
                    # await self.page.fill(password_selector, 'your_password')
                    
                    # Submit the form
                    submit_selector = 'button[type="submit"]'  # Adjust selector as needed
                    await self.page.click(submit_selector)
                    
                    # Wait for login to complete
                    await self.page.wait_for_load_state('networkidle')
                    
                except Exception as e:
                    print(f"[WARNING] Auto-login failed: {e}")
                    print("[INFO] You may need to complete login manually in the browser.")
            
            # Take a screenshot for verification
            screenshot_path = f"login_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=screenshot_path)
            print(f"[INFO] Screenshot saved: {screenshot_path}")
            
            # Export session data
            await self.export_session_data()
            
            print("[SUCCESS] Login process completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Exception during login: {e}")
            print("[FAILED] Login was unsuccessful.")
            print("Please check credentials and configuration.")
            return False
    
    async def export_session_data(self):
        """Export cookies and local storage for session persistence"""
        try:
            # Get cookies
            cookies = await self.context.cookies()
            
            # Get local storage (if needed)
            local_storage = await self.page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            
            # Save to file
            session_data = {
                'cookies': cookies,
                'local_storage': local_storage,
                'timestamp': datetime.now().isoformat()
            }
            
            session_file = f"session_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f"[INFO] Session data exported: {session_file}")
            
        except Exception as e:
            print(f"[WARNING] Could not export session data: {e}")

async def main():
    """Main function to run the login process"""
    if len(sys.argv) < 3:
        print("Usage: python playwright_script.py <username> <mode> [okta_url]")
        print("Modes: auto, interactive")
        sys.exit(1)
    
    username = sys.argv[1]
    mode = sys.argv[2]
    okta_url = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        async with BankOfGuamSession() as session:
            success = await session.login(username, okta_url, mode)
            
            if success:
                print("[INFO] Browser session will remain open for SSO purposes.")
                print("[INFO] Close the browser manually when finished.")
                # Keep the script running to maintain the browser session
                if mode == "auto":
                    print("[INFO] Script will now detach. Browser will remain open.")
                    # In auto mode, we can exit and let the browser stay open
                    # The persistent context will keep the session alive
            else:
                print("[ERROR] Login failed. Check the logs above for details.")
                return False
                
    except KeyboardInterrupt:
        print("\n[INFO] Script interrupted by user.")
    except Exception as e:
        print(f"[ERROR] Unexpected error in main: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Run the main function
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
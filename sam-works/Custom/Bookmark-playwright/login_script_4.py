from playwright.async_api import async_playwright
import yaml
import asyncio

async def login_and_keep_open(app_config, active_browsers):
    """Login and keep browser open for user interaction"""
    # Create playwright instance that won't auto-close
    p = await async_playwright().start()
    
    try:
        browser = await p.chromium.launch(
            headless=False, 
            slow_mo=1000,
            args=['--start-maximized']
        )
        
        # Store browser reference globally for optional cleanup
        active_browsers.append(browser)
        
        context = await browser.new_context()
        page = await context.new_page()

        try:
            login_config = app_config["login"]
            print(f"Starting login process for: {login_config['url']}")
            await page.goto(login_config["url"])
            await page.wait_for_load_state("networkidle")

            # Handle username field
            username_field = page.locator(login_config["username_selector"]).first
            await username_field.wait_for(timeout=10000)

            # Handle password field
            password_field = page.locator(login_config["password_selector"]).first
            await password_field.wait_for(timeout=10000)

            # Handle login button - support both selector and role-based approaches
            if "login_button_selector" in login_config:
                login_button = page.locator(login_config["login_button_selector"]).first
            elif "login_button_role" in login_config and "login_button_name" in login_config:
                login_button = page.get_by_role(
                    login_config["login_button_role"],
                    name=login_config["login_button_name"]
                )
            else:
                raise ValueError("No valid login button config provided.")

            await login_button.wait_for(timeout=10000)

            # Fill credentials
            print("Filling credentials...")
            await username_field.fill(login_config["username"])
            await page.wait_for_timeout(500)
            await password_field.fill(login_config["password"])
            await page.wait_for_timeout(500)

            # Check if button is enabled before clicking
            if await login_button.is_disabled():
                await login_button.wait_for(state="enabled", timeout=10000)

            print("Clicking login button...")
            await login_button.click()
            
            # Wait for navigation or page change
            try:
                await page.wait_for_url("**/*", timeout=15000)
            except:
                # If URL doesn't change, wait for some time to see if login was successful
                await page.wait_for_timeout(3000)

            await page.screenshot(path=f"login_result_{app_config.get('app_name', 'unknown')}.png")
            print("Login complete. Screenshot saved.")
            print("Browser session is now active. User can interact with the browser.")
            print("The script has finished, but the browser will remain open.")
            
            # Keep the function running to prevent browser closure
            while True:
                try:
                    if not browser.is_connected():
                        print("Browser was closed by user.")
                        if browser in active_browsers:
                            active_browsers.remove(browser)
                        break
                    await asyncio.sleep(2)
                except Exception:
                    if browser in active_browsers:
                        active_browsers.remove(browser)
                    break
                
        except Exception as e:
            print(f"Error during login: {e}")
            await page.screenshot(path=f"debug_error_{app_config.get('app_name', 'unknown')}.png")
            print("Error occurred, but browser will remain open for debugging.")
            
            # Keep browser open even on error
            while True:
                try:
                    if not browser.is_connected():
                        if browser in active_browsers:
                            active_browsers.remove(browser)
                        break
                    await asyncio.sleep(2)
                except Exception:
                    if browser in active_browsers:
                        active_browsers.remove(browser)
                    break
            
    except Exception as e:
        print(f"Failed to start browser: {e}")

def load_config():
    """Load configuration from YAML file"""
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def get_app_config(app_name):
    """Get configuration for a specific application"""
    config = load_config()
    if app_name not in config["applications"]:
        raise ValueError(f"Application '{app_name}' not found in configuration")
    
    app_config = config["applications"][app_name].copy()
    app_config["app_name"] = app_name
    return app_config

async def main():
    """Main function for standalone usage"""
    config = load_config()
    active_browsers = []
    
    # Example: Login to the first application in config
    app_names = list(config["applications"].keys())
    if app_names:
        first_app = app_names[0]
        print(f"Logging into: {first_app}")
        app_config = get_app_config(first_app)
        await login_and_keep_open(app_config, active_browsers)
    else:
        print("No applications found in configuration")

if __name__ == "__main__":
    asyncio.run(main())
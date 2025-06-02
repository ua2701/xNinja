from playwright.async_api import async_playwright
import yaml
import asyncio

async def login_and_keep_open(config, active_browsers):
    """Login and keep browser open for user interaction"""
    # Create playwright instance that won't auto-close
    p = await async_playwright().start()
    
    try:
        browser = await p.chromium.launch(
            headless=False, 
            slow_mo=1000,
            args=['--start-maximized']  # Optional: start maximized
        )
        
        # Store browser reference globally for optional cleanup
        active_browsers.append(browser)
        
        context = await browser.new_context()
        page = await context.new_page()

        try:
            print("Starting login process...")
            await page.goto(config["login"]["url"])
            await page.wait_for_load_state("networkidle")

            # Handle username field
            username_field = page.locator(config["login"]["username_selector"]).first
            await username_field.wait_for(timeout=5000)

            # Handle password field
            password_field = page.locator(config["login"]["password_selector"]).first
            await password_field.wait_for(timeout=5000)

            # Handle login button
            if "login_button_selector" in config["login"]:
                login_button = page.locator(config["login"]["login_button_selector"]).first
            elif "login_button_role" in config["login"] and "login_button_name" in config["login"]:
                login_button = page.get_by_role(
                    config["login"]["login_button_role"],
                    name=config["login"]["login_button_name"]
                )
            else:
                raise ValueError("No valid login button config provided.")

            await login_button.wait_for(timeout=5000)

            # Fill credentials
            print("Filling credentials...")
            await username_field.fill(config["login"]["username"])
            await page.wait_for_timeout(500)
            await password_field.fill(config["login"]["password"])
            await page.wait_for_timeout(500)

            # Check if button is enabled before clicking
            if await login_button.is_disabled():
                await login_button.wait_for(state="enabled", timeout=10000)

            print("Clicking login button...")
            await login_button.click()
            await page.wait_for_url("**/*", timeout=10000)

            await page.screenshot(path="login_result.png")
            print("Login complete. Screenshot saved.")
            print("Browser session is now active. User can interact with the browser.")
            print("The script has finished, but the browser will remain open.")
            
            # Keep the function running to prevent browser closure
            # Wait for the browser to be manually closed by user
            while True:
                try:
                    # Check if browser is still connected
                    if not browser.is_connected():
                        print("Browser was closed by user.")
                        # Remove from active browsers list when closed
                        if browser in active_browsers:
                            active_browsers.remove(browser)
                        break
                    # Wait a bit before checking again
                    await asyncio.sleep(2)
                except Exception:
                    # If there's any error checking connection, assume browser is closed
                    if browser in active_browsers:
                        active_browsers.remove(browser)
                    break
                
        except Exception as e:
            print(f"Error during login: {e}")
            await page.screenshot(path="debug_error.png")
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
    
    # Note: We don't call browser.close() or p.stop() here
    # The browser and playwright will remain active

def load_config():
    """Load configuration from YAML file"""
    with open('login.yaml', 'r') as file:
        return yaml.safe_load(file)

async def main():
    """Main function that loads config and runs login with persistent session"""
    config = load_config()
    active_browsers = []  # Local list for standalone usage
    await login_and_keep_open(config, active_browsers)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
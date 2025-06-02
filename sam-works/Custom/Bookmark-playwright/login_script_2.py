from playwright.async_api import async_playwright
import yaml
import asyncio

async def login_and_keep_open(config):
    """Login and keep browser open for user interaction"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, 
            slow_mo=1000,
            args=['--start-maximized']  # Optional: start maximized
        )
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
            
            # Keep the browser open by waiting indefinitely
            # The browser will only close when the user closes it manually
            try:
                # Wait for the browser to be closed by the user
                while not browser.is_connected():
                    await asyncio.sleep(1)
                    break
                
                # Alternative: Wait for browser to close (this will keep the script running)
                await browser.wait_for_event('disconnected')
                
            except Exception:
                # If there's any issue with waiting, just pass
                # The browser will still remain open
                pass
                
        except Exception as e:
            print(f"Error during login: {e}")
            await page.screenshot(path="debug_error.png")
            # Even on error, don't close browser immediately
            print("Error occurred, but browser will remain open for debugging.")
            
        # Note: We don't call browser.close() here
        # The browser will remain open for user interaction

async def login(config):
    """Original login function for backward compatibility"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(config["login"]["url"])
            await page.wait_for_load_state("networkidle")

            username_field = page.locator(config["login"]["username_selector"]).first
            await username_field.wait_for(timeout=5000)

            password_field = page.locator(config["login"]["password_selector"]).first
            await password_field.wait_for(timeout=5000)

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

            await username_field.fill(config["login"]["username"])
            await page.wait_for_timeout(500)
            await password_field.fill(config["login"]["password"])
            await page.wait_for_timeout(500)

            if await login_button.is_disabled():
                await login_button.wait_for(state="enabled", timeout=10000)

            await login_button.click()
            await page.wait_for_url("**/*", timeout=10000)

            await page.screenshot(path="login_result.png")
            print("Login complete. Screenshot saved.")

            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="debug_error.png")
        finally:
            await browser.close()

def load_config():
    """Load configuration from YAML file"""
    with open('login.yaml', 'r') as file:
        return yaml.safe_load(file)

async def main():
    """Main function that loads config and runs login with persistent session"""
    config = load_config()
    await login_and_keep_open(config)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
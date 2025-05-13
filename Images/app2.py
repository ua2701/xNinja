from playwright.sync_api import sync_playwright

EMAIL = "maazahamed27@gmail.com"
CURRENT_PASSWORD = "Password123"
NEW_PASSWORD = "123Password"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)  # GUI + visible steps
    context = None

    try:
        # Try loading existing session
        context = p.chromium.launch_persistent_context(user_data_dir="auth_state", headless=False, slow_mo=100)
        page = context.pages[0] if context.pages else context.new_page()

        # Go directly to password change page (may auto-login via session)
        page.goto("https://magento.softwaretestingboard.com/customer/account/edit/changepass/1/", wait_until="domcontentloaded")

        # If not logged in, login manually
        if page.url.startswith("https://magento.softwaretestingboard.com/customer/account/login"):
            print("Session expired or first-time login — logging in...")

            # Wait for login page elements
            page.wait_for_selector("input#email")
            page.wait_for_selector("input#pass")

            # Fill credentials
            page.fill("input#email", EMAIL)
            page.fill("input#pass", CURRENT_PASSWORD)
            page.click("#send2")


            # Wait for login to complete
            page.wait_for_load_state("networkidle")

            # Revisit the change password page after login
            page.goto("https://magento.softwaretestingboard.com/customer/account/edit/changepass/1/", wait_until="domcontentloaded")

        # Wait for password fields
        page.wait_for_selector("#current-password")
        page.wait_for_selector("#password")
        page.wait_for_selector("#password-confirmation")

        # Fill out change password form
        print("Changing password...")
        page.fill("#current-password", CURRENT_PASSWORD)
        page.fill("#password", NEW_PASSWORD)
        page.fill("#password-confirmation", NEW_PASSWORD)

        # Submit form
        #page.click("button[type=submit]")
        page.click("button.action.save.primary")

        # Wait for response
        page.wait_for_timeout(5000)

        # Check success
        if "You saved the account information." in page.content():
            print("✅ Password changed successfully!")
        else:
            print("⚠️ Password change failed. Check manually.")

    finally:
        if context:
            context.storage_state(path="auth_state.json")  # Save session
            context.close()
        browser.close()

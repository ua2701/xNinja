from playwright.sync_api import sync_playwright

EMAIL = "maazahamed27@gmail.com"
CURRENT_PASSWORD = "Password123"
NEW_PASSWORD = "123Password"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Step 1: Go to login page
    page.goto("https://magento.softwaretestingboard.com/customer/account/login")

    # Step 2: Fill in login credentials
    page.fill('input#email', EMAIL)
    page.fill('input#pass', CURRENT_PASSWORD)

    # Step 3: Click login button
    page.click('button[type=submit]')

    # Step 4: Wait for successful login (you can also check for an element)
    page.wait_for_load_state('networkidle')

    # Step 5: Go to change password page
    page.goto("https://magento.softwaretestingboard.com/customer/account/edit/changepass/1/")

    # Step 6: Fill out change password form
    page.fill("#current-password", CURRENT_PASSWORD)
    page.fill("#password", NEW_PASSWORD)
    page.fill("#password-confirmation", NEW_PASSWORD)

    # Step 7: Submit the form
    page.click("button[type=submit]")

    # Step 8: Wait and check result
    page.wait_for_timeout(5000)  # adjust if needed

    content = page.content()
    if "You saved the account information." in content:
        print("✅ Password changed successfully!")
    else:
        print("⚠️ Something went wrong. Check manually.")

    browser.close()

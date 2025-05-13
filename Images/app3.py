import os
import time
import logging
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configuring logging (UTF-8 encoding)
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"password_change_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Setting encoding (UTF-8) for file handler
file_handler = logging.FileHandler(log_file, encoding='utf-8')
stream_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        stream_handler
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def change_password(email, current_password, new_password):
    """Change password for a single user account"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = None
        
        try:
            context = browser.new_context(storage_state=f"auth_state_{email}.json" if os.path.exists(f"auth_state_{email}.json") else None)
            page = context.new_page()
            
            # Navigate to password change page
            logger.info(f"Navigating to the Application as user {email}")
            page.goto("https://magento.softwaretestingboard.com/customer/account/edit/changepass/1/", 
                      wait_until="domcontentloaded", timeout=10000)
            
            # Check if we need to login
            if page.url.startswith("https://magento.softwaretestingboard.com/customer/account/login"):
                logger.info(f"Attempting to login for the user {email}")
                
                try:
                    # Wait for login page elements
                    page.wait_for_selector("input#email", timeout=5000)
                    page.wait_for_selector("input#pass", timeout=5000)
                    
                    # Fill credentials
                    page.fill("input#email", email)
                    page.fill("input#pass", current_password)
                    page.click("#send2")
                    
                    # Wait for login to complete
                    page.wait_for_selector(".page-title", timeout=10000)
                    
                    if "My Account" in page.content():
                        logger.info(f"Successfully logged in as {email}")
                        
                        # Revisit the change password page after login
                        page.goto("https://magento.softwaretestingboard.com/customer/account/edit/changepass/1/", 
                                  wait_until="domcontentloaded")
                    else:
                        logger.error(f"Login failed for user {email}")
                        return False
                        
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout while trying to login for {email}")
                    return False
            
            # Change password
            try:
                logger.info(f"Filling password change form for {email}")
                
                # Wait for password fields
                page.wait_for_selector("#current-password", timeout=5000)
                page.wait_for_selector("#password", timeout=5000)
                page.wait_for_selector("#password-confirmation", timeout=5000)
                
                # Fill out change password form
                page.fill("#current-password", current_password)
                page.fill("#password", new_password)
                page.fill("#password-confirmation", new_password)
                
                # Submit form
                logger.info(f"Submitting password change for {email}")
                page.click("button.action.save.primary")
                
                # Wait for response and check for success message
                try:
                    page.wait_for_selector(".message-success", timeout=10000)
                    if "You saved the account information." in page.content():
                        logger.info(f"Password changed successfully for {email}")
                        context.storage_state(path=f"auth_state_{email}.json")  # Save session
                        return True
                    else:
                        logger.error(f"Password change failed for {email}")
                        return False
                except PlaywrightTimeoutError:
                    logger.error(f"Password change failed for {email}")
                    return False
                    
            except PlaywrightTimeoutError:
                logger.error(f"Timeout while changing password for {email}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing user {email}: {str(e)}")
            return False
            
        finally:
            if page:
                page.close()
            browser.close()

def main():
    try:
        # Read user data from Excel
        excel_path = "D:\\OneDrive\\Desktop\\Playwright\\SWA_PW.xlsx"
        logger.info(f"Attempting to read Excel file from: {excel_path}")
        
        # Check if file exists
        if not os.path.exists(excel_path):
            logger.error(f"Excel file not found at path: {excel_path}")
            logger.info("Checking current directory...")
            
            # Try finding the file in the current directory
            current_dir = os.getcwd()
            logger.info(f"Current directory: {current_dir}")
            
            possible_files = [f for f in os.listdir(current_dir) if f.endswith('.xlsx')]
            logger.info(f"Excel files found in current directory: {possible_files}")
            
            if possible_files:
                excel_path = os.path.join(current_dir, possible_files[0])
                logger.info(f"Trying with Excel file: {excel_path}")
            else:
                logger.error("No Excel files found in current directory")
                return
        
        try:
            # First, let's print all sheet names
            xls = pd.ExcelFile(excel_path)
            sheet_names = xls.sheet_names
            logger.info(f"Available sheets in Excel file: {sheet_names}")
            
            # Read the first sheet by default
            sheet_name = sheet_names[0]
            logger.info(f"Reading from sheet: {sheet_name}")
            
            # Read with extra visibility into the process
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # Log the column names
            logger.info(f"Columns found in Excel: {df.columns.tolist()}")
            
            # Check if required columns exist
            required_columns = ['Email', 'Current_Password', 'New_Password']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns in Excel: {missing_columns}")
                logger.info("Please ensure your Excel has these column names: Email, Current_Password, New_Password")
                return
            
            # Check if data exists
            if df.empty:
                logger.error("Excel file has no data rows")
                return
                
            # Print first few rows for debugging
            logger.info(f"First few rows of data:\n{df.head().to_string()}")
            
            # Count non-null email values
            valid_users = df[df['Email'].notna()]
            logger.info(f"Found {len(valid_users)} users with email addresses")
            
            if len(valid_users) == 0:
                logger.error("No valid users found in Excel file")
                return
                
            # Process each user
            total_users = len(valid_users)
            successful = 0
            failed = 0
            
            logger.info(f"Found {total_users} users to process")
            
            for index, row in valid_users.iterrows():
                email = row['Email']
                current_password = row['Current_Password']
                new_password = row['New_Password']
                
                logger.info(f"Starting password change process for user: {email}")
                
                result = change_password(email, current_password, new_password)
                
                if result:
                    successful += 1
                else:
                    failed += 1
                    
                # Brief delay between users
                time.sleep(1)
                
            # Log summary
            logger.info("Password change process completed.")
            logger.info(f"Total users: {total_users}")
            logger.info(f"Successful: {successful}")
            logger.info(f"Failed: {failed}")
            
        except Exception as e:
            logger.error(f"Failed to read Excel file: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return
            
    except Exception as e:
        logger.error(f"An error occurred in the main process: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
import os
import time
import logging
import pandas as pd
import random
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

#Do not include =, >, < - HTMLTags as Okta PW Does not support this
def generate_password():
    """Generate a random secure password"""
    # maximum length of password needed
    MAX_LEN = 12

    # declare arrays of the character that we need in out password
    DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    LOCASE_CHARACTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                         'i', 'j', 'k', 'm', 'n', 'o', 'p', 'q',
                         'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
                         'z']

    UPCASE_CHARACTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                         'I', 'J', 'K', 'M', 'N', 'O', 'P', 'Q',
                         'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
                         'Z']

    SYMBOLS = ['@', '#', '$', '%', ':', '?', '.', '/', '|', '~', '*', '(', ')']

    # combines all the character arrays above to form one array
    COMBINED_LIST = DIGITS + UPCASE_CHARACTERS + LOCASE_CHARACTERS + SYMBOLS

    # randomly select at least one character from each character set above
    rand_digit = random.choice(DIGITS)
    rand_upper = random.choice(UPCASE_CHARACTERS)
    rand_lower = random.choice(LOCASE_CHARACTERS)
    rand_symbol = random.choice(SYMBOLS)

    # combine the character randomly selected above
    temp_pass = rand_digit + rand_upper + rand_lower + rand_symbol

    # fill the rest of the password length by selecting randomly from the combined list
    for x in range(MAX_LEN - 4):
        temp_pass = temp_pass + random.choice(COMBINED_LIST)

    # convert temporary password into array and shuffle to prevent pattern
    # Using list instead of array.array('u') to avoid deprecation warning
    temp_pass_list = list(temp_pass)
    random.shuffle(temp_pass_list)

    # traverse the temporary password array and append the chars to form the password
    password = "".join(temp_pass_list)
    
    return password

# Modify the change_password function with these improvements:

def change_password(email, username, current_password):
    """Change password for a single user account and return success status and new password"""
    new_password = generate_password()
    
    # Log new password generation
    logger.info(f"Processing user {email} and generating new password")
    logger.info(f"The new password for the user {email} is {new_password}")
    
    with sync_playwright() as p:
        # Increase timeout and slow_mo values
        browser = p.chromium.launch(headless=False, slow_mo=300)
        #browser = p.chromium.launch(headless=True)
        page = None
        
        try:
            context = browser.new_context(storage_state=f"auth_state_{email}.json" if os.path.exists(f"auth_state_{email}.json") else None)
            page = context.new_page()
            
            # Add longer navigation timeout and better error handling
            logger.info(f"Navigating to the Application as user {email}")
            
            # First navigate to the main site to ensure it's responsive
            logger.info("Navigating to main site first")
            try:
                page.goto("https://magento.softwaretestingboard.com/", 
                          wait_until="networkidle", timeout=20000)
                logger.info("Main site loaded successfully")
            except PlaywrightTimeoutError:
                logger.warning("Main site slow to respond, continuing anyway")
            
            # Now navigate to account page
            try:
                page.goto("https://magento.softwaretestingboard.com/customer/account/", 
                          wait_until="networkidle", timeout=20000)
            except PlaywrightTimeoutError:
                logger.warning("Account page slow to respond, continuing anyway")
            
            # Check if we need to login
            if "Sign In" in page.content() or page.url.startswith("https://magento.softwaretestingboard.com/customer/account/login"):
                logger.info(f"Attempting to login for the user {email}")
                
                try:
                    # Try to navigate directly to login page if not there
                    if not page.url.startswith("https://magento.softwaretestingboard.com/customer/account/login"):
                        page.goto("https://magento.softwaretestingboard.com/customer/account/login/", 
                                  wait_until="networkidle", timeout=20000)
                    
                    # Wait for login page elements with visual confirmation
                    logger.info("Waiting for email field...")
                    page.wait_for_selector("input#email", state="visible", timeout=10000)
                    logger.info("Waiting for password field...")
                    page.wait_for_selector("input#pass", state="visible", timeout=10000)
                    
                    # Fill credentials with small delays
                    logger.info("Filling email...")
                    page.fill("input#email", username)
                    time.sleep(1)
                    logger.info("Filling password...")
                    page.fill("input#pass", current_password)
                    time.sleep(1)
                    
                    logger.info("Clicking login button...")
                    # Try both possible login button selectors
                    try:
                        page.click("#send2", timeout=5000)
                    except:
                        try:
                            page.click("button.action.login.primary", timeout=5000)
                        except:
                            logger.warning("Couldn't find standard login buttons, trying form submission")
                            page.evaluate("document.querySelector('form.form.form-login').submit()")
                    
                    # Wait longer for login to complete
                    logger.info("Waiting for login to complete...")
                    try:
                        page.wait_for_selector(".page-title", state="visible", timeout=20000)
                        logger.info("Found page title after login")
                    except PlaywrightTimeoutError:
                        logger.warning("Timeout waiting for page title, checking if login succeeded anyway")
                    
                    # Check login success more thoroughly
                    time.sleep(3)  # Additional wait to ensure page loads
                    page_content = page.content()
                    if "My Account" in page_content or "Account Information" in page_content:
                        logger.info(f"Successfully logged in as {email}")
                    else:
                        logger.error(f"Login appears to have failed for user {email}")
                        # Check for error messages
                        error_messages = page.evaluate("""
                            () => {
                                const errors = document.querySelectorAll('.message-error');
                                return Array.from(errors).map(e => e.innerText);
                            }
                        """)
                        if error_messages:
                            logger.error(f"Error messages: {error_messages}")
                        return False, None
                        
                except PlaywrightTimeoutError as e:
                    logger.error(f"Timeout while trying to login for {email}: {str(e)}")
                    return False, None
            
            # Navigate directly to edit account page first (more reliable)
            logger.info("Navigating to edit account page")
            try:
                page.goto("https://magento.softwaretestingboard.com/customer/account/edit/", 
                          wait_until="networkidle", timeout=20000)
            except PlaywrightTimeoutError:
                logger.warning("Edit account page slow to respond, continuing anyway")
            
            # Then navigate to change password page
            logger.info("Navigating to change password page")
            try:
                page.goto("https://magento.softwaretestingboard.com/customer/account/edit/changepass/1/", 
                          wait_until="networkidle", timeout=20000)
            except PlaywrightTimeoutError:
                logger.warning("Password change page slow to respond, continuing anyway")
            
            # Change password
            try:
                logger.info(f"Filling password change form for {email}")
                
                # Wait for password fields with visual confirmation
                logger.info("Waiting for current password field...")
                page.wait_for_selector("#current-password", state="visible", timeout=10000)
                logger.info("Waiting for new password field...")
                page.wait_for_selector("#password", state="visible", timeout=10000)
                logger.info("Waiting for confirmation field...")
                page.wait_for_selector("#password-confirmation", state="visible", timeout=10000)
                
                # Fill out change password form with small delays
                logger.info("Filling current password...")
                page.fill("#current-password", current_password)
                time.sleep(1)
                logger.info("Filling new password...")
                page.fill("#password", new_password)
                time.sleep(1)
                logger.info("Filling confirmation password...")
                page.fill("#password-confirmation", new_password)
                time.sleep(1)
                
                # Submit form
                logger.info(f"Submitting password change for {email}")
                try:
                    page.click("button.action.save.primary", timeout=5000)
                except:
                    logger.warning("Couldn't find standard save button, trying form submission")
                    page.evaluate("document.querySelector('form.form-edit-account').submit()")
                
                # Wait for response and check for success message
                try:
                    logger.info("Waiting for success message...")
                    page.wait_for_selector(".message-success", state="visible", timeout=20000)
                    time.sleep(2)  # Additional wait to ensure page loads
                    
                    page_content = page.content()
                    if "You saved the account information" in page_content or "saved" in page_content.lower():
                        logger.info(f"Password changed successfully for {email}")
                        context.storage_state(path=f"auth_state_{email}.json")  # Save session
                        # Take screenshot for confirmation
                        page.screenshot(path=os.path.join(log_dir, f"{email}_success.png"))
                        return True, new_password
                    else:
                        logger.error(f"Password change form submitted but no success message for {email}")
                        # Take screenshot for debugging
                        page.screenshot(path=os.path.join(log_dir, f"{email}_no_success.png"))
                        return False, None
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout waiting for success message for {email}")
                    # Take screenshot for debugging
                    page.screenshot(path=os.path.join(log_dir, f"{email}_timeout.png"))
                    return False, None
                    
            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout while changing password for {email}: {str(e)}")
                # Take screenshot for debugging
                if page:
                    page.screenshot(path=os.path.join(log_dir, f"{email}_error.png"))
                return False, None
                
        except Exception as e:
            logger.error(f"Error processing user {email}: {str(e)}")
            # Take screenshot for debugging
            if page:
                page.screenshot(path=os.path.join(log_dir, f"{email}_exception.png"))
            return False, None
            
        finally:
            if page:
                page.close()
            browser.close()

def safe_save_excel(df, excel_path, sheet_name):
    """Safely save Excel file with multiple retries and backup options"""
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        try:
            attempt += 1
            df.to_excel(excel_path, sheet_name=sheet_name, index=False)
            logger.info(f"Successfully saved Excel file on attempt {attempt}")
            return True
        except PermissionError:
            logger.warning(f"Permission denied on attempt {attempt}. File may be open - waiting 3 seconds...")
            time.sleep(3)
            
            # On last attempt, try saving to a backup file
            if attempt == max_attempts - 1:
                backup_path = f"{excel_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                try:
                    df.to_excel(backup_path, sheet_name=sheet_name, index=False)
                    logger.info(f"Saved to backup file instead: {backup_path}")
                    print(f"\nExcel file saved to backup: {backup_path}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to save backup file: {str(e)}")
        except Exception as e:
            logger.error(f"Error saving Excel file: {str(e)}")
            # Try backup file
            backup_path = f"{excel_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            try:
                df.to_excel(backup_path, sheet_name=sheet_name, index=False)
                logger.info(f"Saved to backup file instead: {backup_path}")
                print(f"\nExcel file saved to backup: {backup_path}")
                return True
            except Exception as e2:
                logger.error(f"Failed to save backup file: {str(e2)}")
                return False
    
    logger.error(f"Failed to save Excel after {max_attempts} attempts")
    return False

def main():
    try:
        # Read user data from Excel
        excel_path = r"D:\OneDrive\Book.xlsx"
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
            required_columns = ['Email', 'Application_Username', 'Current_Password']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns in Excel: {missing_columns}")
                logger.info("Please ensure your Excel has all required columns")
                return
            
            # Create App_Status column if it doesn't exist
            if 'App_Status' not in df.columns:
                df['App_Status'] = None
                logger.info("Added App_Status column to the dataframe")
            
            # Ensure proper data types to avoid warnings
            df['App_Status'] = df['App_Status'].astype(str)
            
            # Check if data exists
            if df.empty:
                logger.error("Excel file has no data rows")
                return
                
            # Print first few rows for debugging
            logger.info(f"First few rows of data:\n{df.head().to_string()}")
            
            # Total users in Excel
            total_in_excel = len(df)
            logger.info(f"Total users in Excel: {total_in_excel}")
            
            # Process users - only those that don't have App_Status='P'
            to_process = df[(df['App_Status'] != 'P') & (df['Email'].notna())]
            total_users = len(to_process)
            
            logger.info(f"Users to process: {total_users}")
            successful = 0
            failed = 0
            
            # Create in-memory results tracking
            results = []
            
            for index, row in to_process.iterrows():
                email = row['Email']
                username = row['Application_Username']
                current_password = row['Current_Password']
                
                logger.info(f"Processing user {index+1}/{total_users}: {email}")
                
                # Change password
                result, new_password = change_password(email, username, current_password)
                
                # Store results in memory first
                results.append({
                    'index': index,
                    'email': email,
                    'result': result,
                    'new_password': new_password
                })
                
                if result:
                    successful += 1
                else:
                    failed += 1
                
                # Brief delay between users
                time.sleep(1)
            
            # Now apply all changes to the dataframe
            for item in results:
                index = item['index']
                if item['result']:
                    df.at[index, 'Current_Password'] = item['new_password']
                    df.at[index, 'App_Status'] = 'P'
                    logger.info(f"Updated password for {item['email']} in dataframe")
                else:
                    df.at[index, 'App_Status'] = 'F'
                    logger.info(f"Marked {item['email']} as failed in dataframe")
            
            # Final save with safe function
            save_result = safe_save_excel(df, excel_path, sheet_name)
            
            # Log results regardless of save success
            logger.info("Password change process completed.")
            logger.info(f"Total users: {total_users}")
            logger.info(f"Successful: {successful}")
            logger.info(f"Failed: {failed}")
            logger.info(f"Excel save successful: {save_result}")
            logger.info(f"Summary report saved to {os.path.join(log_dir, f'password_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt')}")
            
            # Create a summary report file as backup
            summary_file = os.path.join(log_dir, f"password_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(summary_file, 'w') as f:
                f.write(f"Password Change Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total users processed: {total_users}\n")
                f.write(f"Successful: {successful}\n")
                f.write(f"Failed: {failed}\n\n")
                
                f.write("Details:\n")
                for item in results:
                    status = "SUCCESS" if item['result'] else "FAILED"
                    password_info = f"New password: {item['new_password']}" if item['result'] else "Password unchanged"
                    f.write(f"{item['email']} - {status} - {password_info}\n")
            
            # Just print Excel file updated status as requested
            if save_result:
                logger.info("Excel file updated successfully")
            else:
                logger.error("Excel update failed - check logs")
            
        except Exception as e:
            logger.error(f"Failed to process Excel file: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return
            
    except Exception as e:
        logger.error(f"An error occurred in the main process: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
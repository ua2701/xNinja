import os
import time
import logging
import pandas as pd
import random
import array
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

    SYMBOLS = ['@', '#', '$', '%', '=', ':', '?', '.', '/', '|', '~', '>',
               '*', '(', ')', '<']

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

    logger.info(f"Generated new password (length: {len(password)})")
    return password

def change_password(email, username, current_password):
    """Change password for a single user account and return success status and new password"""
    new_password = generate_password()
    
    # Display the new password on console
    print(f"\n{'='*50}")
    print(f"NEW PASSWORD FOR {email}: {new_password}")
    print(f"{'='*50}\n")
    
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
                    page.fill("input#email", username)
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
                        return False, None
                        
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout while trying to login for {email}")
                    return False, None
            
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
                        
                        # Display success message with new password again
                        print(f"\n{'='*50}")
                        print(f"PASSWORD CHANGE SUCCESSFUL FOR {email}")
                        print(f"NEW PASSWORD: {new_password}")
                        print(f"{'='*50}\n")
                        
                        context.storage_state(path=f"auth_state_{email}.json")  # Save session
                        return True, new_password
                    else:
                        logger.error(f"Password change failed for {email}")
                        return False, None
                except PlaywrightTimeoutError:
                    logger.error(f"Password change failed for {email}")
                    return False, None
                    
            except PlaywrightTimeoutError:
                logger.error(f"Timeout while changing password for {email}")
                return False, None
                
        except Exception as e:
            logger.error(f"Error processing user {email}: {str(e)}")
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
        excel_path = "D:\\OneDrive\\Desktop\\Playwright\\SWA_PW_2.xlsx"
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
            
            # Process users - only those that don't have App_Status='P'
            to_process = df[(df['App_Status'] != 'P') & (df['Email'].notna())]
            total_users = len(to_process)
            
            logger.info(f"Found {total_users} users to process")
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
            
            logger.info(f"Summary report saved to {summary_file}")
            
            # Display summary with passwords on console
            print("\n" + "="*60)
            print("PASSWORD CHANGE SUMMARY")
            print("="*60)
            print(f"Total users processed: {total_users}")
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")
            print("\nPASSWORD DETAILS:")
            print("-"*60)
            for item in results:
                status = "SUCCESS" if item['result'] else "FAILED"
                if item['result']:
                    print(f"{item['email']} - {status} - New password: {item['new_password']}")
                else:
                    print(f"{item['email']} - {status} - Password unchanged")
            print("="*60)
            print(f"Summary report saved to: {summary_file}")
            if save_result:
                print(f"Excel file updated successfully")
            else:
                print(f"Excel update failed - check logs")
            print("="*60)
            
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
import os
import csv
import requests
import json
import yaml
#import urllib3
from datetime import datetime

#urllib3.disable_warnings()

bt_domain = ""
bt_api_key = ""
bt_api_user = ""
session = None

def load_env_config():
    global bt_domain, bt_api_key, bt_api_user
    
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key == 'BEYONDTRUST_DOMAIN':
                        bt_domain = value
                    elif key == 'BEYONDTRUST_API_KEY':
                        bt_api_key = value
                    elif key == 'BEYONDTRUST_API_USER':
                        bt_api_user = value
    except Exception as e:
        print(f"Error reading .env file: {e}")
        return False
    
    if not bt_domain or not bt_api_key or not bt_api_user:
        print("Error: Missing configuration in .env file")
        return False
    
    return True

def load_yaml_config():
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        print(f"Error reading config.yaml file: {e}")
        return None

def create_session():
    global session
    session = requests.Session()
	session.verify = False #disable SSL verification
    session.verify = "cacert.pem"

def signin_bt():
    print("Signing in to BeyondTrust...")
    
    headers = {
        "Authorization": f"PS-Auth key={bt_api_key}; runas={bt_api_user};",
        "Content-Type": "application/json"
    }
    session.headers.update(headers)
    
    url = f"https://{bt_domain}/BeyondTrust/api/public/v3/Auth/SignAppin"
    
    try:
        response = session.post(url)
        if response.status_code == 200:
            print("Successfully signed in to BeyondTrust")
            return True
        else:
            print(f"Sign in failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error during sign in: {e}")
        return False

def signout_bt():
    print("Signing out from BeyondTrust...")
    
    url = f"https://{bt_domain}/BeyondTrust/api/public/v3/Auth/Signout"
    
    try:
        response = session.post(url)
        if response.status_code == 200:
            print("Successfully signed out from BeyondTrust")
        else:
            print("Sign out failed")
    except Exception as e:
        print(f"Error during sign out: {e}")

def read_csv_data(file_path):
    print(f"Reading CSV file: {file_path}")
    
    data = []
    
    try:
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)  # gett first row as headers
            
            headers_lower = [h.lower().strip() for h in headers]  # header conversion to lowercase
            
            for row in reader:
                if len(row) >= 3:  # atleast Title, Username, Password
                    record = {}
                    
                    # mapping CSV columns -> fields
                    for i, header in enumerate(headers_lower):
                        if i < len(row):
                            if 'title' in header:
                                record['Title'] = row[i].strip()
                            elif 'username' in header or 'user' in header:
                                record['Username'] = row[i].strip()
                            elif 'password' in header or 'pass' in header:
                                record['Password'] = row[i].strip()
                            elif 'description' in header or 'desc' in header:
                                record['Description'] = row[i].strip()
                            elif 'notes' in header or 'note' in header:
                                record['Notes'] = row[i].strip()
                            elif 'url' in header or 'website' in header:
                                record['URL'] = row[i].strip()
                    
                    # check if required fields are present
                    if record.get('Title') and record.get('Username') and record.get('Password'):
                        # set default values (null) for optional fields
                        if 'Description' not in record:
                            record['Description'] = ""
                        if 'Notes' not in record:
                            record['Notes'] = ""
                        if 'URL' not in record:
                            record['URL'] = ""
                            
                        data.append(record)
                    else:
                        print(f"Skipping row due to missing required fields: {row}")
        
        print(f"Found {len(data)} valid records in CSV")
        return data
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def create_secret(folder_id, credential_data, owner_id):
    
    # request body
    request_body = {
        "Title": credential_data['Title'],
        "Username": credential_data['Username'],
        "Password": credential_data['Password'],
        "OwnerId": owner_id, 
        "OwnerType": "Group",  
        "Description": credential_data['Description'],
        "Notes": credential_data['Notes']
    }
    
    if credential_data['URL']:
        request_body["Urls"] = [credential_data['URL']]
    
    url = f"https://{bt_domain}/BeyondTrust/api/public/v3/Secrets-Safe/Folders/{folder_id}/secrets"
    
    try:
        response = session.post(url, json=request_body)
        
        if response.status_code == 200 or response.status_code == 201:
            return True, "Success"
        else:
            return False, f"API returned status code: {response.status_code}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def write_log_file(results):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"bulk_load_results_{timestamp}.csv"
    
    try:
        with open(log_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['S.No', 'Title', 'Username', 'Status', 'Message', 'Timestamp'])
        
            for i, result in enumerate(results, 1):
                writer.writerow([
                    i,
                    result['title'],
                    result['username'],
                    result['status'],
                    result['message'],
                    result['timestamp']
                ])
        
        print(f"Results logged to: {log_filename}")
        
    except Exception as e:
        print(f"Error writing log file: {e}")

def main():
    print("=== Credential Bulk Loader ===")
    print()

    # Load environment conf
    if not load_env_config():
        return
    
    # Load YAML conf
    config = load_yaml_config()
    if not config:
        return

    csv_file_path = config.get('csv_file_path')
    folder_id = config.get('folder_id')
    owner_id = config.get('owner_id')

    if not csv_file_path or not folder_id or not owner_id:
        print("Error: Missing csv_file_path, folder_id, or owner_id in config.yaml")
        return

    print(f"CSV File: {csv_file_path}")
    print(f"Folder ID: {folder_id}")
    print(f"Owner ID: {owner_id}")
    print()

    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found: {csv_file_path}")
        return
    
    if not str(folder_id).strip():
        print("Error: Folder ID cannot be empty!")
        return
		
	if not owner_id:
        print("Error: Owner ID cannot be empty!")
        return
    
    # create session
    create_session()
    
    # sign in to BT
    if not signin_bt():
        print("Cannot proceed without successful sign in")
        return
    
    try:
        # read CSV data
        credentials = read_csv_data(csv_file_path)
        
        if not credentials:
            print("No valid credentials found in CSV")
            return
        
        # add the message about onboarding credentials
        print(f"Onboarding credentials into folder ID: {folder_id}")
        print()
        
        # processing each credential
        results = []
        success_count = 0
        
        print("Processing credentials...")
        print("-" * 50)
        
        for credential in credentials:
            username = credential['Username']
            #title = credential['Title']
            
            # username and status
            #print(f"Processing: {title} (User: {username}) = ", end="")
			#print(f"Processing: {username} = ", end="")
            
            success, message = create_secret(folder_id, credential, owner_id)
            
            result = {
                'title': credential['Title'],
                'username': username,
                'status': 'SUCCESS' if success else 'FAILED',
                'message': message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            results.append(result)
            
            if success:
                print("SUCCESS")
                success_count += 1
            else:
				#print("FAILED")
                print(f"FAILED - {message}")
        
        print()
        #print("=== SUMMARY ===")
        print(f"Total processed: {len(credentials)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(credentials) - success_count}")
        print()
        
        # write log file
        write_log_file(results)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # sign out
        signout_bt()
    
    print("Script Ends...")

if __name__ == "__main__":
    main()
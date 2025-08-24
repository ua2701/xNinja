# BeyondTrust Secret Updater
A Python script to update and convert BeyondTrust secrets ownership from **User** to **Group** in bulk.

---

## Overview
This script automates the process of updating BeyondTrust Secret Safe entries.  
It reads secrets from a specified folder, retrieves their details, and updates them to use **Group ownership** instead of **User ownership**, while preserving existing metadata and passwords.

---

## Project Structure
```
├── secret_updater.py        # Main script
├── config.yaml              # Configuration file (folder & owner details)
├── .env                     # BeyondTrust API credentials (template)
├── cacert.pem               # SSL certificate bundle
└── README.md                # This file
```

---

## Prerequisites
- Python **3.6 or higher**
- Access to **BeyondTrust Secret Safe API**

---

## Installation
1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd bt-secret-updater
   ```

2. **Install Required Dependencies**
   ```bash
   pip install requests pyyaml
   ```

3. **Configure Your Environment** (see [Configuration](#configuration))

---

## Configuration

### 1. Environment Variables (`.env`)
```
BEYONDTRUST_DOMAIN=the-beyondtrust-domain-here
BEYONDTRUST_API_KEY=the-api-key-here
BEYONDTRUST_API_USER=the-api-username-here
```

### 2. YAML Configuration (`config.yaml`)
```yaml
folder_id: "<your-folder-id>"
owner_id: "<target-group-owner-id>"
```

### 3. SSL Certificate (`cacert.pem`)
Ensure that `cacert.pem` contains the SSL certificate bundle required for your BeyondTrust domain.

---

## Usage
1. Prepare `.env` and `config.yaml` with required values.  
2. Run the script:
   ```bash
   python secret_updater.py
   ```

---

## Processing Flow
1. Load API credentials from `.env`  
2. Load folder and owner configuration from `config.yaml`  
3. Authenticate to BeyondTrust API  
4. Retrieve all secrets in the given folder  
5. Filter secrets owned by **User**  
6. For each matching secret:  
   - Retrieve its password text  
   - Update secret ownership from **User** → **Group**  
7. Print summary of processed secrets  
8. Sign out from BeyondTrust  

---

## Output
- **Console Output**:  
  - Logs of secrets being processed  
  - Success or failure messages per secret  
  - Summary with total, successful, and failed updates  

Example:
```
=== BeyondTrust Secret Updater ===

Folder ID: 1234
Owner ID: 5678

Signing in to BeyondTrust...
Successfully signed in to BeyondTrust

Getting secrets from folder: 1234
Found 15 total secrets in folder
Secrets with OwnerType 'User': 10
Secrets with OwnerType 'Group' (skipped): 5

Processing 10 secrets with OwnerType 'User'...
--------------------------------------------------
Processing: DB Admin (Username: dbadmin, OwnerType: User)
SUCCESS   : DB Admin

Total secrets with OwnerType 'User' processed: 10
Successfully updated (User -> Group): 9
Failed to update: 1

Signing out from BeyondTrust...
Successfully signed out from BeyondTrust
Script Ends...
```

---

## API Endpoints Used
- **POST** `/BeyondTrust/api/public/v3/Auth/SignAppin` → Authenticate/Sign in  
- **GET** `/BeyondTrust/api/public/v3/Secrets-Safe/Folders/{folder_id}/secrets` → Get secrets from folder  
- **GET** `/BeyondTrust/api/public/v3/Secrets-Safe/Secrets/{secret_id}/text` → Get secret password text  
- **PUT** `/BeyondTrust/api/public/v3/Secrets-Safe/secrets/{secret_id}` → Update secret details  
- **POST** `/BeyondTrust/api/public/v3/Auth/Signout` → Sign out  

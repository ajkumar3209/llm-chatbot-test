# ZOHO TOKEN AUTO-REFRESH CONFIGURATION

## Implementation Complete
I have updated the code on the server (`zoho_api_simple.py`) with automatic token refresh logic.

**How it works:**
1. System catches HTTP 401 (Unauthorized) errors from SalesIQ or Desk
2. It attempts to refresh the access token using the stored `REFRESH_TOKEN` + Client Credentials
3. If successful, it updates the token in memory and retries the failed request immediately
4. If failed, it logs the error

## REQUIRED ACTION: Add Client Credentials

For the refresh logic to work, you MUST add your Zoho OAuth Client Secret to the `.env` file. These were missing from the configuration.

### 1. Locate Credentials
Go to [Zoho Developer Console](https://api-console.zoho.com/) or [Zoho Accounts](https://accounts.zoho.com/developer/console):
- Open your connected Web/Self Client App
- Find **Client ID**
- Find **Client Secret**

### 2. Update Server Environment
Run the following commands to add these keys to your server:

```bash
ssh -i "C:\Users\aryan.gupta\Downloads\acebuddy.key" ubuntu@45.194.90.181

# Edit the environment file
sudo nano /opt/llm-chatbot/.env
```

**Add these lines to the bottom of the file:**
```ini
# Zoho OAuth Credentials (REQUIRED for Auto-Refresh)
ZOHO_CLIENT_ID=your_client_id_here
ZOHO_CLIENT_SECRET=your_client_secret_here
```
*(Replace with your actual values)*

### 3. Restart Service
After saving the file (Ctrl+O, Enter, Ctrl+X), restart the bot:

```bash
sudo systemctl restart llm-chatbot
```

### 4. Verify
Once configured, you don't need to manually update tokens every hour. The system will auto-rotate them using the Refresh Token.

**Note:** Ensure your `SALESIQ_REFRESH_TOKEN` and `DESK_REFRESH_TOKEN` in the `.env` file are valid. If they are expired or revoked, you'll need to generate them fresh one last time.

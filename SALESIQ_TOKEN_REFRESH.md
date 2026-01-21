# SALESIQ TOKEN EXPIRED - REFRESH GUIDE

## Problem Identified

Your SalesIQ transfer is failing with:
```
HTTP 400
{"error":{"code":1001,"message":"Unknown authentication error, Contact SalesIQ Team!"}}
```

**Root Cause**: SalesIQ OAuth tokens expire in **1 hour**. Your token was generated at ~10:37 UTC and is now expired (it's 11:07 UTC).

Current token: `1000.326c0f0100f95666953c10160f036827.532a48809842bd1b45e8380efdd674e3`

## Solution: Refresh the SalesIQ Token

### Option 1: Automatic Refresh (If Implemented)

The system has a `SALESIQ_REFRESH_TOKEN` available:
```
SALESIQ_REFRESH_TOKEN=1000.0c1efffbe42040df71a126fe1f6378a6.e6867cfdc8ae2a8cb83097c8ff28d07c
```

**To implement automatic refresh in code:**

You need to add token refresh logic to handle expiration automatically. This prevents the need to manually regenerate tokens.

### Option 2: Manual Token Regeneration (Immediate Fix)

1. Go to **Zoho SalesIQ**: https://salesiq.zoho.in
2. Click **Settings** → **Developers** → **OAuth Applications**
3. Find your application and click **Edit**
4. Click **Generate Token** or **Re-authorize**
5. You'll be redirected to login
6. Click **Accept** to authorize
7. Copy the new **Access Token**

### Step 3: Update Server with New Token

Once you have the new access token:

```bash
# SSH into server
ssh -i /path/to/acebuddy.key ubuntu@45.194.90.181

# Edit environment file
sudo nano /opt/llm-chatbot/.env

# Find this line:
SALESIQ_ACCESS_TOKEN=1000.326c0f0100f95666953c10160f036827.532a48809842bd1b45e8380efdd674e3

# Replace with your NEW token (paste the new one)
SALESIQ_ACCESS_TOKEN=1000.YOUR_NEW_TOKEN_HERE.NEW_PART_HERE

# Save and exit (Ctrl+X, Y, Enter)

# Restart service
sudo systemctl restart llm-chatbot

# Verify it's running
sudo systemctl status llm-chatbot
```

### Step 4: Test the Transfer

1. Click **Instant Chat** button again in SalesIQ widget
2. Check logs:
```bash
ssh -i /path/to/acebuddy.key ubuntu@45.194.90.181 "sudo journalctl -u llm-chatbot -n 20 --no-pager | grep -A5 'INSTANT\|CHAT TRANSFER\|SalesIQ API'"
```

3. Should see success response like:
```
SalesIQ: Response Status: 201
```

## Long-term Solution: Implement Token Refresh

To prevent this from happening again every hour, the application should:

1. **Implement refresh token logic** - When access token expires, use the refresh token to get a new one
2. **Cache the new token** - Store updated token in memory or database
3. **Retry on 401** - When SalesIQ returns 401, automatically refresh and retry

The refresh token is already configured:
```
SALESIQ_REFRESH_TOKEN=1000.0c1efffbe42040df71a126fe1f6378a6.e6867cfdc8ae2a8cb83097c8ff28d07c
```

If you want this implemented, let me know and I can add auto-refresh logic to the `zoho_api_simple.py` file.

## Summary

| Item | Status | Action |
|------|--------|--------|
| Token Format | ✓ Valid | No change needed |
| Token Scopes | ✓ Correct | No change needed |
| Token Expiration | ✗ **EXPIRED** | **Regenerate new token** |
| Refresh Token | ✓ Available | Can be used for auto-refresh |

## Next Steps

1. **Generate new SalesIQ token** from Zoho SalesIQ dashboard
2. **Update** `/opt/llm-chatbot/.env` with new token
3. **Restart** the service
4. **Test** Instant Chat button again - it should work now
5. *(Optional)* Request token auto-refresh implementation to prevent this issue

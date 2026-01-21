# DESK TOKEN SCOPE MISMATCH - FIX GUIDE

## Problem Identified
Your current Desk token has **NO API scopes** configured:
```
Token: 1005.4377f5f8d68766fae0ce3d70a267c2a4.6b4ff3550b6627f9eb251f0439e135e5
Endpoint: desk.zoho.in ✓ (correct)
Scopes: NONE ✗ (causing 403 SCOPE_MISMATCH error)
```

All requests to `/api/v1/calls`, `/api/v1/tickets`, `/api/v1/departments` return:
```
{"errorCode":"SCOPE_MISMATCH","message":"The OAuth Token does not contain the scope to perform this operation."}
```

## Solution: Regenerate Desk Token with Correct Scopes

### Step 1: Go to Zoho Desk Account

1. Login to **Zoho Desk**: https://desk.zoho.in
2. Click **Settings** (bottom-left gear icon)
3. Go to **Developers** → **API** (or **OAuth Applications**)

### Step 2: Find Your OAuth Application

1. Look for your existing OAuth application (or create new one)
2. Click **Edit** on the application
3. Go to the **Scope** section

### Step 3: Add Required Scopes

For **Callback functionality**, enable these scopes:
- `Desk.calls.CREATE` ✓ Required
- `Desk.calls.READ` ✓ Required
- `Desk.calls.UPDATE` ✓ Optional but recommended
- `Desk.tickets.CREATE` ✓ Good to have as fallback
- `Desk.tickets.READ` ✓ Good to have
- `Desk.contacts.READ` ✓ For looking up contacts (optional)
- `Desk.contacts.CREATE` ✓ For creating contacts (optional)

**Minimum Required:**
- `Desk.calls.CREATE`
- `Desk.calls.READ`

### Step 4: Regenerate/Authorize Token

1. After updating scopes, you need to **re-authorize** to get a new token
2. Delete the old token (if option available)
3. Click **Generate Token** or re-authorize the application
4. You'll be redirected to Zoho login
5. Click **Accept** to authorize with new scopes
6. Copy the new **Access Token** provided

### Step 5: Update Server Environment

Once you have the new token:

```bash
ssh -i /path/to/acebuddy.key ubuntu@45.194.90.181

# Edit the .env file
sudo nano /opt/llm-chatbot/.env

# Find the DESK_ACCESS_TOKEN line and replace with your new token
# Example:
DESK_ACCESS_TOKEN=1005.NEW_TOKEN_HERE.NEW_PART_HERE

# Save and exit (Ctrl+X, Y, Enter)

# Restart the service
sudo systemctl restart llm-chatbot

# Verify service is running
sudo systemctl status llm-chatbot
```

### Step 6: Verify Token Works

Run this test command (replace with your new token):

```bash
ssh -i /path/to/acebuddy.key ubuntu@45.194.90.181 "curl -s -X GET 'https://desk.zoho.in/api/v1/departments' -H 'Authorization: Zoho-oauthtoken YOUR_NEW_TOKEN_HERE' -H 'orgId: 60000688226' | head -c 200"
```

**Expected response** (should NOT contain "SCOPE_MISMATCH"):
```json
{"data":[{"id":"2782000000002013","name":"Department Name",...}]}
```

## Troubleshooting

**If you still get SCOPE_MISMATCH:**
- Confirm you've re-authorized the app with new scopes
- Check that `Desk.calls.CREATE` is explicitly enabled in OAuth app settings
- Try logging out and back into Zoho to clear cache
- Wait 5-10 minutes for scope changes to propagate

**If you get INVALID_OAUTH:**
- Token format is wrong
- Token has expired
- Regenerate a fresh token

**If you get different error:**
- Token is valid but something else wrong
- Share the error message for debugging

## Summary of Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Desk endpoint | ✓ Correct | desk.zoho.in is the right endpoint |
| Token format | ✓ Valid | Token is recognized by Zoho |
| Token scopes | ✗ MISSING | Token has NO scopes - needs regeneration |
| Callback creation | ✗ BLOCKED | Cannot create calls until scopes fixed |
| Transfer buttons | ✓ Working | SalesIQ transfer functionality is OK |

## Next Steps

1. **Regenerate Desk token with `Desk.calls.CREATE` scope**
2. **Update `/opt/llm-chatbot/.env` with new token**
3. **Restart service**: `sudo systemctl restart llm-chatbot`
4. **Test in SalesIQ widget** - "Schedule Callback" button should now work

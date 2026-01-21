# TOKEN GENERATION GUIDE

## Current Problem
Your `.env` file has **mixed/wrong tokens**:
- `SALESIQ_ACCESS_TOKEN` = `1005.xxx` (This is a DESK token, not SalesIQ!)
- `DESK_ACCESS_TOKEN` = `1005.xxx` (This might be outdated/expired)

## What You Need

### Token Format Recognition
- **SalesIQ tokens** start with `1000.`
- **Desk tokens** start with `1005.`
- **Other Zoho services** have different prefixes

You need **THREE FRESH TOKENS**:

| Operation | Service | Token Prefix | Where to Generate |
|-----------|---------|--------------|------------------|
| Chat Transfer | SalesIQ | `1000.xxx` | Zoho SalesIQ OAuth |
| Chat Closure | SalesIQ | `1000.xxx` | Zoho SalesIQ OAuth |
| Callback Creation | Desk | `1005.xxx` | Zoho Desk OAuth |

---

## Step-by-Step Token Generation

### 1. GENERATE SALESIQ TOKEN (for Chat Transfer & Closure)

**URL:** https://salesiq.zoho.in/

1. Login to Zoho SalesIQ
2. Click **Settings** (bottom-left gear icon)
3. Go to **Developers** → **OAuth Applications** (or **API**)
4. Click your app name (or create new if none exists)
5. Click **Generate Token** or **Authorize**
6. You'll see:
   ```
   Access Token: 1000.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx
   Refresh Token: 1000.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx
   ```
7. **Copy both** - these are your `SALESIQ_ACCESS_TOKEN` and `SALESIQ_REFRESH_TOKEN`

**In .env:**
```ini
SALESIQ_ACCESS_TOKEN=1000.your_access_token_here
SALESIQ_REFRESH_TOKEN=1000.your_refresh_token_here
```

---

### 2. GENERATE DESK TOKEN (for Callback Creation)

**URL:** https://desk.zoho.in/

1. Login to Zoho Desk
2. Click **Settings** (bottom-right gear icon)
3. Go to **Developers** → **API** or **OAuth Applications**
4. Click your app name (or create new if none exists)
5. Click **Generate Token** or **Authorize**
6. You'll see:
   ```
   Access Token: 1005.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx
   Refresh Token: 1005.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx
   ```
7. **Copy both** - these are your `DESK_ACCESS_TOKEN` and `DESK_REFRESH_TOKEN`

**In .env:**
```ini
DESK_ACCESS_TOKEN=1005.your_access_token_here
DESK_REFRESH_TOKEN=1005.your_refresh_token_here
```

---

## Required Scopes

### For SalesIQ Token
When generating/authorizing, ensure these scopes are enabled:
- ✓ `SalesIQ.conversations.CREATE` (for chat transfer)
- ✓ `SalesIQ.conversations.READ` (for reading conversation data)
- ✓ `SalesIQ.conversations.UPDATE` (optional, for updating)

### For Desk Token  
When generating/authorizing, ensure these scopes are enabled:
- ✓ `Desk.calls.CREATE` (for creating callbacks)
- ✓ `Desk.calls.READ` (for reading call data)
- ✓ `Desk.departments.READ` (for fetching department list)

---

## Complete .env Template

After generating tokens, update your `.env` to look like this:

```ini
# ═════════════════════════════════════════════════════════════
# SALESIQ TOKENS (Chat Transfer & Closure)
# ═════════════════════════════════════════════════════════════
SALESIQ_ACCESS_TOKEN=1000.your_salesiq_access_token
SALESIQ_REFRESH_TOKEN=1000.your_salesiq_refresh_token
SALESIQ_APP_ID=2782000012893013
SALESIQ_DEPARTMENT_ID=2782000000002013
SALESIQ_SCREEN_NAME=rtdsportal

# ═════════════════════════════════════════════════════════════
# DESK TOKENS (Callback Creation)
# ═════════════════════════════════════════════════════════════
DESK_ACCESS_TOKEN=1005.your_desk_access_token
DESK_REFRESH_TOKEN=1005.your_desk_refresh_token
DESK_ORG_ID=60000688226
DESK_DEPARTMENT_ID=2782000000002013

# ═════════════════════════════════════════════════════════════
# OAUTH CLIENT CREDENTIALS (for Auto-Refresh)
# ═════════════════════════════════════════════════════════════
# These should be the same Client ID/Secret used to generate tokens
ZOHO_CLIENT_ID=your_client_id_from_api_console
ZOHO_CLIENT_SECRET=your_client_secret_from_api_console
```

---

## Testing After Token Update

Once you have the correct tokens:

1. **Update .env** with the new tokens
2. **Run the test script**:
   ```bash
   python test_tokens_locally.py
   ```
3. **Expected output**: All three tests should PASS (✓)
4. **Then deploy to server**: Copy updated `.env` to production and restart service

---

## Troubleshooting

### If you get "Invalid OAuthToken" (Error 1008)
→ Token is expired or malformed
→ Generate a fresh token

### If you get "SCOPE_MISMATCH" (HTTP 403)
→ Token doesn't have required scopes enabled
→ Re-authorize app with broader scopes

### If you get "Invalid Method" (Error 1010)
→ API endpoint doesn't exist or is wrong
→ Verify the correct SalesIQ API version

---

## Quick Checklist

- [ ] Generated fresh SALESIQ token (starts with `1000.`)
- [ ] Generated fresh DESK token (starts with `1005.`)
- [ ] Updated `.env` with both tokens
- [ ] Ran `test_tokens_locally.py` and all tests PASSED
- [ ] Ready to deploy to production server

#!/usr/bin/env python3
"""
Refresh SalesIQ Token and Update .env
"""
import requests
import re
import os

CLIENT_ID = "1005.2CC62FI55NQZG6QT3FM8HDRIMMV2ZP"
CLIENT_SECRET = "dc4e57f035c348f3e463c5fb03fa98fb318dee9740"
REFRESH_TOKEN = "1005.ca064ba4e1942c852537587184b9a71d.fdfd4da49245cce8fa14bd5af8d2192e"
ENV_FILE = ".env"

print("=" * 80)
print("🔄 REFRESHING SalesIQ TOKEN")
print("=" * 80)

token_url = "https://accounts.zoho.in/oauth/v2/token"

token_params = {
    "refresh_token": REFRESH_TOKEN,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "refresh_token"
}

try:
    print(f"\n📍 Requesting fresh token from Zoho...")
    response = requests.post(token_url, params=token_params, timeout=10)
    
    print(f"✓ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        new_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS! Fresh token obtained!")
        print("=" * 80)
        print(f"\n🔑 New Access Token (first 50 chars):\n{new_token[:50]}...")
        print(f"\n⏱️  Expires in: {expires_in} seconds ({expires_in/3600:.1f} hours)")
        
        # Read current .env file
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r") as f:
                env_content = f.read()
            
            # Replace the token
            updated_content = re.sub(
                r'SALESIQ_ACCESS_TOKEN=.*',
                f'SALESIQ_ACCESS_TOKEN={new_token}',
                env_content
            )
            
            # Write back
            with open(ENV_FILE, "w") as f:
                f.write(updated_content)
            
            print(f"\n✅ Updated {ENV_FILE} with new token")
            print(f"\n📝 New Token (for reference):")
            print(f"{new_token}")
        else:
            print(f"\n⚠️  {ENV_FILE} not found!")
            print(f"\n📝 Add this to your .env:")
            print(f"SALESIQ_ACCESS_TOKEN={new_token}")
        
        print("\n" + "=" * 80)
        print("✅ Token refresh complete!")
        print("=" * 80)
        
    else:
        print(f"\n❌ Token refresh failed!")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

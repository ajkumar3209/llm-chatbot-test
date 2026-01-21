"""Refresh Desk token to get a fresh one"""
import requests
import json

# OAuth credentials for Desk
CLIENT_ID = "1000.H3IA38PCNL66OFLJERMQI9YTYRWJAW"
CLIENT_SECRET = "c6997926776a6ee27b9977620735a639911dcda120"
REFRESH_TOKEN = "1000.f768be1e156b4637f88858b0773b7b6b.0d4a7753b5f446ef5c0a7d2c9cad2b68"

print("=" * 80)
print("Getting FRESH Desk token...")
print("=" * 80)

token_url = "https://accounts.zoho.in/oauth/v2/token"
token_params = {
    "refresh_token": REFRESH_TOKEN,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "refresh_token"
}

response = requests.post(token_url, params=token_params)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    new_token = data.get("access_token")
    
    print(f"\n✅ Fresh token obtained!")
    print(f"\nNew Token: {new_token}")
    print(f"\nAdd this to server .env:")
    print(f"DESK_ACCESS_TOKEN={new_token}")
else:
    print(f"❌ Failed: {response.text}")

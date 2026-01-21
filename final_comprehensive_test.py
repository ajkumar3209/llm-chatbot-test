"""
FINAL COMPREHENSIVE TEST - Transfer & Callback
Run this after Desk API IP whitelist is updated
"""
import requests
import json
from datetime import datetime

print("=" * 80)
print("COMPREHENSIVE API TEST")
print("=" * 80)

BASE_URL = "http://45.194.90.181:8000"
timestamp = int(datetime.now().timestamp())

# TEST 1: TRANSFER (Should already work)
print("\n" + "=" * 80)
print("TEST 1: TRANSFER BUTTON")
print("=" * 80)

transfer_payload = {
    'visitor_name': 'Test Visitor',
    'visitor_email': f'test_{timestamp}@test.com',
    'department': 'support',
    'session_id': f'test_transfer_{timestamp}'
}

response = requests.post(f'{BASE_URL}/api/transfer', json=transfer_payload, timeout=10)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Response: {json.dumps(result, indent=2)}")

if result.get('success'):
    print("✅ TRANSFER WORKING!")
else:
    print(f"❌ Transfer failed: {result.get('error')}")

# TEST 2: CALLBACK (Might now work if IP is whitelisted)
print("\n" + "=" * 80)
print("TEST 2: CALLBACK BUTTON")
print("=" * 80)

callback_payload = {
    'visitor_email': f'callback_{timestamp}@test.com',
    'visitor_phone': '9999999999',
    'visitor_name': 'Test User',
    'session_id': f'test_callback_{timestamp}'
}

response = requests.post(f'{BASE_URL}/api/callback', json=callback_payload, timeout=10)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Response: {json.dumps(result, indent=2)}")

if result.get('success'):
    print("✅ CALLBACK WORKING!")
else:
    print(f"❌ Callback failed: {result.get('error')}")

# TEST 3: CHECK WHICH BUTTONS ARE READY
print("\n" + "=" * 80)
print("BUTTON STATUS")
print("=" * 80)

buttons_status = {
    "Transfer": "✅ READY" if (response.status_code == 200) else "❌ NOT READY",
    "Callback": "✅ READY" if (result.get('success')) else "⏳ PENDING IP WHITELIST",
    "Closure": "⏳ NOT TESTED YET"
}

for button, status in buttons_status.items():
    print(f"  {button}: {status}")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("If Callback still fails with 'Token refresh failed':")
print("  1. Go to Zoho Desk > Settings > Security (or Developer Settings)")
print("  2. Find 'API IP Whitelist' or 'IP Restrictions'")
print("  3. Add: 61.95.184.222")
print("  4. Save and wait 5 minutes")
print("  5. Run this script again")
print("=" * 80)

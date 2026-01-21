#!/usr/bin/env python3
"""
CALLBACK ENDPOINT FIX - Root Cause and Solution
================================================

ROOT CAUSE IDENTIFIED:
The callback endpoint was failing because the Desk API organization ID (org_id) was incorrect.

OLD (WRONG):
  DESK_ORG_ID=61309000000170001

CORRECT:
  DESK_ORG_ID=60000688226

This mismatch caused the Desk API to return:
  Status: 422
  Error: {"errorCode":"UNPROCESSABLE_ENTITY","message":"The value passed for the 'orgId' parameter is invalid."}

WHAT TO DO:
1. Update the .env file on your production server with:
   DESK_ACCESS_TOKEN=1000.8769640e906622e1fabf4c0cbc281df6.5ed01d9206bd19f4ebdf286aef552e28
   DESK_REFRESH_TOKEN=1000.f768be1e156b4637f88858b0773b7b6b.0d4a7753b5f446ef5c0a7d2c9cad2b68
   DESK_ORG_ID=60000688226

2. Restart the service:
   sudo systemctl restart llm-chatbot.service

3. Test the callback endpoint
"""

import requests
import json
from datetime import datetime

print(__doc__)

# Test with CORRECT credentials
DESK_TOKEN = "1000.8769640e906622e1fabf4c0cbc281df6.5ed01d9206bd19f4ebdf286aef552e28"
DESK_ORG = "60000688226"  # CORRECT ORG ID
DEPT_ID = "8454000000019805"

timestamp = int(datetime.now().timestamp())

print("\n" + "="*70)
print("LOCAL TEST: Contact creation with CORRECT org_id")
print("="*70)

headers = {
    "Authorization": f"Zoho-oauthtoken {DESK_TOKEN}",
    "orgId": DESK_ORG,  # CORRECT ORG ID
    "Content-Type": "application/json"
}

payload = {
    "lastName": "Test",
    "firstName": "User",
    "email": f"test_{timestamp}@test.com",
    "phone": "9999999999"
}

print(f"\n📤 Creating contact with CORRECT org_id...")
print(f"   OrgId: {DESK_ORG}")
print(f"   Email: {payload['email']}")

response = requests.post(
    "https://desk.zoho.in/api/v1/contacts",
    headers=headers,
    json=payload,
    timeout=10
)

print(f"\n📥 Response:")
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    contact_id = result.get("id")
    print(f"   ✅ SUCCESS! Contact created: {contact_id}")
    print(f"   Email: {result.get('email')}")
    print(f"   Name: {result.get('firstName')} {result.get('lastName')}")
elif response.status_code == 422:
    result = response.json()
    print(f"   ❌ UNPROCESSABLE ENTITY (wrong org_id)")
    print(f"   Error: {json.dumps(result, indent=2)}")
else:
    print(f"   ❌ Error: {response.text[:300]}")

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("1. SSH to production server: ssh ubuntu@45.194.90.181")
print("2. Edit .env file: nano .env")
print("3. Update these lines:")
print("   DESK_ACCESS_TOKEN=1000.8769640e906622e1fabf4c0cbc281df6.5ed01d9206bd19f4ebdf286aef552e28")
print("   DESK_REFRESH_TOKEN=1000.f768be1e156b4637f88858b0773b7b6b.0d4a7753b5f446ef5c0a7d2c9cad2b68")
print("   DESK_ORG_ID=60000688226")
print("4. Save and restart service:")
print("   sudo systemctl restart llm-chatbot.service")
print("5. Test: python test_production_endpoints.py")
print("="*70)

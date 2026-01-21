"""
Close conversation via API
"""
import requests
import json

closure_token = "1000.8728de25f129335caf043a9196091798.3e3fd67e184ee28e0fa9ba44a3c35b61"
screen_name = "rtdsportal"
conversation_id = "2782000013425081"

print("=" * 70)
print("CLOSING CONVERSATION VIA API")
print("=" * 70)
print(f"Conversation ID: {conversation_id}")
print()

headers = {
    "Authorization": f"Zoho-oauthtoken {closure_token}",
    "Content-Type": "application/json"
}

close_url = f"https://salesiq.zoho.in/api/v2/{screen_name}/conversations/{conversation_id}/close"

print(f"Endpoint: {close_url}")
print()

try:
    response = requests.put(close_url, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✅ CONVERSATION CLOSED SUCCESSFULLY!")
        print()
        print(f"Chat ID: {data.get('data', {}).get('chat_id')}")
        print(f"Reference ID: {data.get('data', {}).get('reference_id')}")
        attender = data.get('data', {}).get('attender', {})
        print(f"Attender: {attender.get('name')}")
        print()
        print("Response:")
        print(json.dumps(data, indent=2)[:500])
    else:
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

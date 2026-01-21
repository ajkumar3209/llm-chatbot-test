"""
Debug Desk API access
"""

import requests

token = '1000.5874f03163ddb90c89f905dc54e95372.7a9624803958bdc8e1a3a7d0d67773a1'
org_id = '60000688226'

headers = {
    'Authorization': f'Zoho-oauthtoken {token}',
    'orgId': org_id
}

print('Testing Desk.calls endpoint access...')
print()

# Test 1: Read calls
print('Test 1: Reading calls (GET)')
print('-'*60)
url = 'https://desk.zoho.in/api/v1/calls'
response = requests.get(url, headers=headers, timeout=10)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    calls = data.get('data', [])
    print(f'✓ Can read calls: Found {len(calls)} existing calls')
else:
    print(f'✗ Cannot read calls')
    print(f'Response: {response.text[:300]}')

print()

# Test 2: List departments
print('Test 2: List departments')
print('-'*60)
url = 'https://desk.zoho.in/api/v1/departments'
response = requests.get(url, headers=headers, timeout=10)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    depts = data.get('data', [])
    print(f'✓ Found {len(depts)} departments')
    if depts:
        for dept in depts:
            print(f"  - {dept.get('name')} (ID: {dept.get('id')})")
else:
    print(f'✗ Cannot list departments')
    print(f'Response: {response.text[:300]}')

print()

# Test 3: Try to understand why POST is forbidden
print('Test 3: Testing POST with minimal payload')
print('-'*60)
url = 'https://desk.zoho.in/api/v1/calls'
minimal_payload = {
    'departmentId': '2782000000002013'
}
headers_with_content = headers.copy()
headers_with_content['Content-Type'] = 'application/json'

response = requests.post(url, json=minimal_payload, headers=headers_with_content, timeout=10)
print(f'Status: {response.status_code}')
print(f'Response: {response.text[:300]}')

print()
print('='*60)
print('DIAGNOSIS:')
print('='*60)
print('If Test 1 passes (status 200) but Test 3 fails (status 403):')
print('  → Issue is with CREATE permission, not scope')
print('  → Need to check account role/permissions in Desk')
print()
print('If Test 1 fails (status 403):')
print('  → Issue is with READ permission itself')
print('  → Token may be invalid or org setting blocks API access')

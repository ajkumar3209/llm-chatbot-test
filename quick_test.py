"""Quick test for the simplified chatbot"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_case(name, message, session_id="test_123"):
    """Test a single case"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"User: {message}")
    
    payload = {
        "message": {"text": message},
        "session_id": session_id,
        "visitor": {"name": "Test User"}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/webhook", json=payload, timeout=30)
        result = response.json()
        
        print(f"\nBot: {result.get('reply', 'N/A')}")
        
        if 'suggestions' in result:
            print(f"\n✅ ESCALATION BUTTONS SHOWN:")
            for btn in result['suggestions']:
                print(f"   - {btn['title']}")
        
        if 'ticket_id' in result:
            print(f"\n✅ DESK TICKET CREATED: {result['ticket_id']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None

# Test cases
print("STARTING CHATBOT TESTS")
print("="*70)

# Test 1: RDP file not working - should ask diagnostic question
test_case(
    "RDP file not working",
    "my rdp file is not working"
)

# Test 2: Reset session
test_case(
    "Session reset",
    "new issue"
)

# Test 3: RDP file missing - should give URL immediately
test_case(
    "RDP file missing",
    "i lost my rdp file"
)

# Test 4: New session for next test
test_case(
    "Session reset",
    "new issue",
    session_id="test_456"
)

# Test 5: Login issue - should ask for error
test_case(
    "Login issue",
    "can't login",
    session_id="test_456"
)

# Test 6: New session
test_case(
    "Session reset",
    "new issue",
    session_id="test_789"
)

# Test 7: Black screen - should escalate immediately
test_case(
    "Black screen",
    "my screen is completely black after logging in",
    session_id="test_789"
)

# Test 8: New session
test_case(
    "Session reset",
    "new issue",
    session_id="test_999"
)

# Test 9: Outside KB - should say not in KB
test_case(
    "Outside knowledge base",
    "how do I configure VPN?",
    session_id="test_999"
)

# Test 10: New session
test_case(
    "Session reset",
    "new issue",
    session_id="test_111"
)

# Test 11: User requests agent
test_case(
    "User wants agent",
    "can I talk to someone?",
    session_id="test_111"
)

print(f"\n{'='*70}")
print("ALL TESTS COMPLETED")
print(f"{'='*70}")

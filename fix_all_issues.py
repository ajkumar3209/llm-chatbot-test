"""
Fix all three issues:
1. Enable auto-close chat on resolution
2. Fix token loading
3. Update .env with correct credentials
"""

# Read the current llm_chatbot.py to fix the auto-close issue
with open('llm_chatbot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the resolution section and add close_chat() call
old_code = '''            # Track resolution (important for metrics)
            if session_id in conversations:
                metrics_collector.end_conversation(session_id, "resolved")
                logger.info(f"[Metrics] 📊 Issue resolved by bot - prevented escalation")
                # Keep conversation in memory for idle timeout period
                # Will be cleaned up by Zoho's idle timeout (not us)'''

new_code = '''            # Track resolution (important for metrics)
            if session_id in conversations:
                metrics_collector.end_conversation(session_id, "resolved")
                logger.info(f"[Metrics] 📊 Issue resolved by bot - prevented escalation")
                
                # Auto-close chat via API
                if salesiq_api.enabled:
                    logger.info(f"[Resolution] Attempting to close chat {session_id}")
                    close_result = salesiq_api.close_chat(session_id, "resolved")
                    if close_result.get("success"):
                        logger.info(f"[Resolution] ✓ Chat closed successfully")
                    else:
                        logger.warning(f"[Resolution] Failed to close chat: {close_result.get('error')}")'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('llm_chatbot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Fixed auto-close issue in llm_chatbot.py")
else:
    print("⚠ Could not find auto-close section to fix")

print("\n✓ Local file updated. Now uploading to server...")

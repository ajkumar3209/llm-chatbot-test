#!/bin/bash
cd /opt/llm-chatbot

# Restore original server tokens for close_chat (v2 API)
cp .env.backup .env

# Set VISITOR tokens to the org token (for transfer)
sed -i 's|^SALESIQ_VISITOR_ACCESS_TOKEN=.*|SALESIQ_VISITOR_ACCESS_TOKEN=1005.c6964961de514067dede6226b14eda46.466e836f62c25e204c9b2ede9410fe9d|' .env
sed -i 's|^SALESIQ_VISITOR_REFRESH_TOKEN=.*|SALESIQ_VISITOR_REFRESH_TOKEN=1005.cb46276e2f2ab7d7acef749c82ba3362.a344e22be50aa2a0384bdf6ef302a001|' .env
sed -i 's|^SALESIQ_VISITOR_CLIENT_ID=.*|SALESIQ_VISITOR_CLIENT_ID=1005.96DY5WJOOAU7O4PNUPXPK5LPSP81CV|' .env
sed -i 's|^SALESIQ_VISITOR_CLIENT_SECRET=.*|SALESIQ_VISITOR_CLIENT_SECRET=bf2b2824abe490c2dde3dfbc8433366cb0f9cf1467|' .env

echo "✓ Fixed: Server tokens for close_chat, Org tokens for transfer"

#!/bin/bash
cd /opt/llm-chatbot

# Backup current .env
cp .env .env.backup

# Remove old SALESIQ entries and create new file
grep -v "^SALESIQ_" .env > .env.new

# Add new SALESIQ credentials
cat >> .env.new << 'EOF'
SALESIQ_ACCESS_TOKEN=1005.c6964961de514067dede6226b14eda46.466e836f62c25e204c9b2ede9410fe9d
SALESIQ_REFRESH_TOKEN=1005.cb46276e2f2ab7d7acef749c82ba3362.a344e22be50aa2a0384bdf6ef302a001
SALESIQ_CLIENT_ID=1005.96DY5WJOOAU7O4PNUPXPK5LPSP81CV
SALESIQ_CLIENT_SECRET=bf2b2824abe490c2dde3dfbc8433366cb0f9cf1467
EOF

# Replace old .env
mv .env.new .env

echo "✓ SalesIQ credentials updated"

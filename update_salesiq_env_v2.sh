#!/bin/bash
cd /opt/llm-chatbot

# Restore from backup
cp .env.backup .env

# Replace only the 4 main SALESIQ credentials (not VISITOR ones)
sed -i 's|^SALESIQ_ACCESS_TOKEN=.*|SALESIQ_ACCESS_TOKEN=1005.c6964961de514067dede6226b14eda46.466e836f62c25e204c9b2ede9410fe9d|' .env
sed -i 's|^SALESIQ_REFRESH_TOKEN=.*|SALESIQ_REFRESH_TOKEN=1005.cb46276e2f2ab7d7acef749c82ba3362.a344e22be50aa2a0384bdf6ef302a001|' .env
sed -i 's|^SALESIQ_CLIENT_ID=.*|SALESIQ_CLIENT_ID=1005.96DY5WJOOAU7O4PNUPXPK5LPSP81CV|' .env
sed -i 's|^SALESIQ_CLIENT_SECRET=.*|SALESIQ_CLIENT_SECRET=bf2b2824abe490c2dde3dfbc8433366cb0f9cf1467|' .env

echo "✓ Updated main SALESIQ credentials (kept VISITOR, APP_ID, DEPARTMENT_ID)"

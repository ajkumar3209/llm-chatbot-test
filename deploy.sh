#!/bin/bash
# QUICK DEPLOY SCRIPT - Run this on the Ubuntu server
# Usage: bash deploy.sh

echo "================================"
echo "Deploying production code"
echo "================================"

# Backup old files
sudo cp /opt/llm-chatbot/zoho_api_simple.py /opt/llm-chatbot/zoho_api_simple.py.backup.$(date +%s)
sudo cp /opt/llm-chatbot/llm_chatbot.py /opt/llm-chatbot/llm_chatbot.py.backup.$(date +%s)

# Deploy new files
sudo cp /tmp/zoho_api_simple.py /opt/llm-chatbot/zoho_api_simple.py
sudo cp /tmp/llm_chatbot.py /opt/llm-chatbot/llm_chatbot.py

echo "✓ Files deployed"

# Restart service
sudo systemctl restart llm-chatbot.service

echo "✓ Service restarted"

# Wait for startup
sleep 5

# Check status
echo ""
echo "Service status:"
sudo systemctl status llm-chatbot.service --no-pager -n 5

echo ""
echo "Recent logs:"
sudo journalctl -u llm-chatbot -n 30 --no-pager

echo ""
echo "================================"
echo "✅ Deployment complete!"
echo "================================"

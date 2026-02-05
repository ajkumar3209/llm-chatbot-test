#!/bin/bash
# Production Deployment Script for LLM-First Chatbot Refactor
# This script safely deploys the refactored version with rollback capability

set -e  # Exit on error

PROD_SERVER="ubuntu@acebuddy"
PROD_PATH="/opt/llm-chatbot"
LOCAL_PATH="$(pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="llm_chatbot_backup_${TIMESTAMP}.py"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  LLM-First Chatbot - Production Deployment Script      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Validate local files
echo "📋 Step 1: Validating local files..."
if [ ! -f "$LOCAL_PATH/llm_chatbot.py" ]; then
    echo "❌ ERROR: llm_chatbot.py not found in current directory"
    exit 1
fi

if [ ! -f "$LOCAL_PATH/zoho_api_simple.py" ]; then
    echo "❌ ERROR: zoho_api_simple.py not found in current directory"
    exit 1
fi
echo "✅ Local files validated"
echo ""

# Step 2: Check Python syntax
echo "📋 Step 2: Checking Python syntax..."
python3 -m py_compile "$LOCAL_PATH/llm_chatbot.py" || {
    echo "❌ ERROR: Syntax error in llm_chatbot.py"
    exit 1
}
python3 -m py_compile "$LOCAL_PATH/zoho_api_simple.py" || {
    echo "❌ ERROR: Syntax error in zoho_api_simple.py"
    exit 1
}
echo "✅ Syntax check passed"
echo ""

# Step 3: Backup current production files
echo "📋 Step 3: Creating backup on production server..."
ssh $PROD_SERVER "cd $PROD_PATH && cp llm_chatbot.py $BACKUP_NAME && ls -lh $BACKUP_NAME" || {
    echo "❌ ERROR: Failed to create backup"
    exit 1
}
echo "✅ Backup created: $BACKUP_NAME"
echo ""

# Step 4: Copy files to production
echo "📋 Step 4: Copying refactored files to production..."
scp "$LOCAL_PATH/llm_chatbot.py" "$PROD_SERVER:$PROD_PATH/" || {
    echo "❌ ERROR: Failed to copy llm_chatbot.py"
    exit 1
}
scp "$LOCAL_PATH/zoho_api_simple.py" "$PROD_SERVER:$PROD_PATH/" || {
    echo "❌ ERROR: Failed to copy zoho_api_simple.py"
    exit 1
}
echo "✅ Files copied successfully"
echo ""

# Step 5: Verify syntax on production
echo "📋 Step 5: Verifying syntax on production server..."
ssh $PROD_SERVER "cd $PROD_PATH && python3 -m py_compile llm_chatbot.py && python3 -m py_compile zoho_api_simple.py" || {
    echo "❌ ERROR: Syntax error detected on production server"
    echo "🔄 Rolling back to previous version..."
    ssh $PROD_SERVER "cd $PROD_PATH && cp $BACKUP_NAME llm_chatbot.py"
    exit 1
}
echo "✅ Production syntax verified"
echo ""

# Step 6: Stop the service
echo "📋 Step 6: Stopping LLM chatbot service..."
ssh $PROD_SERVER "sudo systemctl stop llm-chatbot.service" || {
    echo "❌ ERROR: Failed to stop service"
    exit 1
}
sleep 2
echo "✅ Service stopped"
echo ""

# Step 7: Start the service
echo "📋 Step 7: Starting LLM chatbot service..."
ssh $PROD_SERVER "sudo systemctl start llm-chatbot.service" || {
    echo "❌ ERROR: Failed to start service"
    echo "🔄 Rolling back to previous version..."
    ssh $PROD_SERVER "cd $PROD_PATH && cp $BACKUP_NAME llm_chatbot.py && sudo systemctl start llm-chatbot.service"
    exit 1
}
sleep 3
echo "✅ Service started"
echo ""

# Step 8: Check service status
echo "📋 Step 8: Checking service status..."
ssh $PROD_SERVER "sudo systemctl status llm-chatbot.service --no-pager" || {
    echo "❌ ERROR: Service failed to start"
    echo "🔄 Rolling back to previous version..."
    ssh $PROD_SERVER "cd $PROD_PATH && cp $BACKUP_NAME llm_chatbot.py && sudo systemctl restart llm-chatbot.service"
    exit 1
}
echo ""

# Step 9: Monitor logs for errors
echo "📋 Step 9: Monitoring logs for startup errors (10 seconds)..."
ssh $PROD_SERVER "journalctl -u llm-chatbot.service -n 20 --no-pager" || true
echo ""

echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ DEPLOYMENT SUCCESSFUL!                             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Deployment Summary:"
echo "   • Backup: $BACKUP_NAME"
echo "   • Service: Running"
echo "   • Next Steps: Run test_responses.sh to validate LLM responses"
echo ""
echo "🔄 To rollback if needed:"
echo "   ssh $PROD_SERVER 'cd $PROD_PATH && cp $BACKUP_NAME llm_chatbot.py && sudo systemctl restart llm-chatbot.service'"
echo ""

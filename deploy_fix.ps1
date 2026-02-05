# Quick Deploy Script - Fix ClassificationResult
# Run this when you reach office

Write-Host "🚀 Deploying fixed llm_chatbot.py..." -ForegroundColor Green

# Copy to server
scp -i "C:\Users\aryan.gupta\Downloads\acebuddy.key" llm_chatbot.py ubuntu@45.194.90.181:/opt/llm-chatbot/llm_chatbot.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ File copied successfully" -ForegroundColor Green
    
    # Verify and restart
    ssh -i "C:\Users\aryan.gupta\Downloads\acebuddy.key" ubuntu@45.194.90.181 "
    cd /opt/llm-chatbot
    echo '🔍 Checking syntax...'
    python3 -m py_compile llm_chatbot.py && echo '✅ Syntax OK' || echo '❌ Syntax Error'
    
    echo ''
    echo '🔄 Restarting service...'
    sudo systemctl restart llm-chatbot.service
    sleep 3
    
    echo ''
    echo '📊 Service status:'
    sudo systemctl status llm-chatbot.service --no-pager | head -8
    
    echo ''
    echo '✅ Deployment complete! Test the chat widget now.'
    "
} else {
    Write-Host "❌ Failed to copy file" -ForegroundColor Red
}

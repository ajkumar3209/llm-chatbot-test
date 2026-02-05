@echo off
REM Quick Railway Deploy for Testing
REM This script deploys the fixed llm_chatbot.py to Railway

echo.
echo 🚀 Deploying to Railway...
echo.

REM Check if git is initialized
if not exist ".git" (
    echo ⚠️  Git not initialized. Initializing...
    git init
    git remote add railway https://github.com/<your-repo>.git
    if errorlevel 1 (
        echo ❌ Error: Update the remote URL in this script!
        pause
        exit /b 1
    )
)

echo ✅ Adding files...
git add llm_chatbot.py requirements.txt

echo ✅ Committing...
git commit -m "Fix: Add @dataclass decorator to ClassificationResult - resolves message error"

echo ✅ Pushing to Railway...
git push railway main

if errorlevel 1 (
    echo ❌ Push failed! Check your git remote.
    pause
    exit /b 1
)

echo.
echo ✅ Deployment pushed!
echo.
echo 📊 Now:
echo 1. Go to https://railway.app
echo 2. Check Deployments tab
echo 3. Wait for build to complete (2-5 minutes)
echo 4. Check Logs for "Expert prompt loaded successfully"
echo 5. Test the SalesIQ chat widget
echo.
pause

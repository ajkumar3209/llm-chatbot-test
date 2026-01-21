#!/usr/bin/env python3
"""Organize documentation and test files into proper directory structure"""

import os
import shutil
from pathlib import Path

base_dir = Path.cwd()

# Define which files go to which directories
docs_dirs = {
    'architecture': [
        'ALL_PHASES_COMPLETE.md', 'PHASE_4_COMPLETE.md', 'PHASE_0_COMPLETE.md',
        'CODE_ANALYSIS_IMPLEMENTATION_PLAN.md', 'IMPLEMENTATION_SUMMARY.md',
        'FINAL_IMPLEMENTATION_SUMMARY.md'
    ],
    'deployment': [
        'DEPLOYMENT_CHECKLIST.md', 'FINAL_DEPLOYMENT_CHECKLIST.md', 'QUICK_START.md',
        'SETUP_AND_DEPLOYMENT.md', 'QUICK_DEPLOY.md', 'RAILWAY_ENV_SETUP.md',
        'COMPLETE_SETUP_GUIDE.md'
    ],
    'api': [
        'SALESIQ_API_SIMPLE_GUIDE.md', 'SALESIQ_REAL_TRANSFER_GUIDE.md', 'SALESIQ_TRANSFER_FIX.md',
        'API_SCOPES_REQUIRED.md', 'ZOHO_API_SCOPES_CORRECT_FORMAT.md', 'TOKEN_REFRESH_README.md',
        'PAYLOAD_VALIDATION_GUIDE.md'
    ],
    'guides': [
        'COMPREHENSIVE_ANSWERS.md', 'SALESIQ_TEST_GUIDE.md', 'QUICK_REFERENCE.md',
        'WIDGET_DISPLAY_GUIDE.md', 'TEST_CHAT_FLOWS.md', 'SALESIQ_WIDGET_TEST_GUIDE.md'
    ]
}

moved_count = 0

# Move docs to organized directories
print("=" * 60)
print("ORGANIZING DOCUMENTATION FILES")
print("=" * 60)

for category, files in docs_dirs.items():
    for file in files:
        src = base_dir / file
        dst = base_dir / 'docs' / category / file
        if src.exists():
            try:
                shutil.move(str(src), str(dst))
                moved_count += 1
                print(f"✓ Moved {file:45} → docs/{category}/")
            except Exception as e:
                print(f"✗ Error moving {file}: {e}")

# Move test files
print("\n" + "=" * 60)
print("ORGANIZING TEST FILES")
print("=" * 60)

test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
for file in test_files:
    src = base_dir / file
    dst = base_dir / 'tests' / file
    if src.exists():
        try:
            shutil.move(str(src), str(dst))
            moved_count += 1
            print(f"✓ Moved {file:45} → tests/")
        except Exception as e:
            print(f"✗ Error moving {file}: {e}")

# List old/obsolete files to delete
print("\n" + "=" * 60)
print("IDENTIFYING OBSOLETE FILES FOR DELETION")
print("=" * 60)

obsolete_files = [
    'ACTUAL_NUMBERS_ANALYSIS.md',
    'ALL_FIXES_SUMMARY.md',
    'ANSWER_YOUR_QUESTION.md',
    'API_IMPLEMENTATION_READY.md',
    'BOT_RESPONSE_IMPROVEMENTS.md',
    'BUILD_IN_PROGRESS.txt',
    'BUTTON_VS_TEXT_SUMMARY.md',
    'BUTTONS_IMPLEMENTED.md',
    'CHAT_CLOSURE_EXPLANATION.md',
    'CHAT_FLOW_FIXES.md',
    'DEPLOYMENT_READY.txt',
    'DEPLOY_BUTTONS.md',
    'DEPLOY_FIXES.md',
    'DEPLOY_NOW.md',
    'DEPLOY_NOW_FIXED.md',
    'DEPLOY_TRANSFER_FIX.md',
    'DISK_SPACE_FIX.md',
    'DOCUMENTATION_INDEX.md',
    'EMERGENCY_FIX_BASIC_WEBHOOK.md',
    'ESCALATION_OPTIONS_GUIDE.md',
    'ESCALATION_SUMMARY.md',
    'FIXED_API_INTEGRATION.md',
    'FIXES_APPLIED.md',
    'FIXES_SUMMARY.md',
    'HALLUCINATION_PREVENTION.md',
    'IMPLEMENTATION_COMPLETE.md',
    'IMPLEMENTATION_RECOMMENDATION.md',
    'LATEST_STATUS.md',
    'LOCAL_TEST_RESULTS.md',
    'OPERATOR_HANDOFF_EXPLANATION.md',
    'PHASE_0_PROGRESS.md',
    'PRESENTATION_OPTIONS.md',
    'QUICK_REFERENCE.md',
    'README_FIXES.md',
    'README_FIXES.txt',
    'READY_TO_TEST.md',
    'RESPONSE_QUALITY_FIX.md',
    'SALESIQ_BUTTONS_FIX.md',
    'SALESIQ_DEPARTMENT_FIX.md',
    'SALESIQ_JSON_PAYLOAD_REFERENCE.md',
    'SALESIQ_TRANSFER_FIXED.md',
    'SALESIQ_VISITOR_API_FIX.md',
    'SCOPES_FIX.md',
    'START_HERE.md',
    'START_HERE_PHASE_0.md',
    'TOKEN_USAGE_ANALYSIS.md',
    'TROUBLESHOOTING_MESSAGE_HANDLER.md',
    'VERIFY_FIX.md',
    'VISITOR_API_FIX_COMPLETE.md',
    'VISUAL_FLOW_COMPARISON.md',
    'WEBHOOK_FIXES_APPLIED.md',
    'WEBHOOK_FIX_DEPLOYMENT.md',
    'WHILE_BUILDING.md',
    'WORK_COMPLETED.md',
    'YOUR_QUESTIONS_ANSWERED.md',
    'RAILWAY_BUILD_MONITORING.md',
    'RAILWAY_DEPLOYMENT_FIX.md',
    'RAILWAY_FIX_INDENTATION.md'
]

deleted_count = 0
for file in obsolete_files:
    file_path = base_dir / file
    if file_path.exists():
        try:
            file_path.unlink()
            deleted_count += 1
            print(f"✓ Deleted {file:45}")
        except Exception as e:
            print(f"✗ Error deleting {file}: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"✓ Moved:     {moved_count} files to organized directories")
print(f"✓ Deleted:   {deleted_count} obsolete files")
print(f"✓ Remaining: README.md, llm_chatbot.py, requirements.txt, etc.")
print("\n" + "=" * 60)
print("DIRECTORY STRUCTURE")
print("=" * 60)
print("""
Ragv1/
├── README.md                 (Main documentation)
├── llm_chatbot.py           (Main application)
├── requirements.txt         (Dependencies)
├── .env.example            (Environment template)
│
├── config/                 (Configuration)
│   └── prompts/
│       └── expert_system_prompt.txt
│
├── services/               (Core services)
│   ├── router.py
│   ├── state_manager.py
│   ├── metrics.py
│   ├── handler_registry.py
│   └── handlers/
│       ├── base.py
│       ├── escalation_handlers.py
│       └── issue_handlers.py
│
├── docs/                   (Documentation)
│   ├── architecture/       (System design & phases)
│   ├── deployment/         (Deployment guides)
│   ├── api/               (API documentation)
│   └── guides/            (User guides & reference)
│
├── tests/                 (Test files)
│   ├── test_bot_comprehensive.py
│   ├── test_router_integration.py
│   └── ...
│
├── integrations/          (Third-party integrations)
├── Chat Transcripts/      (Sample chat data)
└── processed_data/        (Data files)
""")

print("✓ Organization complete! Ready for Git commit.")

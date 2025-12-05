"""
Add disk space KB article to Pinecone
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "support-chatbot"
EMBEDDING_MODEL = "text-embedding-3-small"

# Get index host
headers = {"Api-Key": PINECONE_API_KEY, "Content-Type": "application/json"}
response = requests.get("https://api.pinecone.io/indexes", headers=headers, verify=False)
indexes = response.json()
INDEX_HOST = None
for idx in indexes.get('indexes', []):
    if idx['name'] == INDEX_NAME:
        INDEX_HOST = idx['host']
        break

# Create the KB article
kb_article = {
    "title": "How to fix low disk space on server",
    "text": """How to fix low disk space on server

Issue: Disk space low / Disk space full / Disk space showing red

Step 1: Clear Temporary Files
Press Win + R on your keyboard.
Type %temp% and press Enter.
A folder will open — press Ctrl + A to select all files.
Press Delete to remove temporary files.
Skip any files that cannot be deleted.

Step 2: Clear System Temp Folder
Press Win + R again.
Type temp and press Enter.
Select all files (Ctrl + A).
Press Delete.
Skip files that are in use.

Step 3: Empty Recycle Bin
Right-click on Recycle Bin on the desktop.
Click Empty Recycle Bin.
Confirm the action to free up space.

Step 4: Remove Unused / Old Files
Open File Explorer.
Check folders like Downloads, Documents, and Desktop.
Select files you no longer need.
Right-click → Delete.

Benefits:
- Free up disk space quickly
- Improve server performance
- Prevent disk full errors
- Easy to do without technical knowledge"""
}

print("Creating KB article for disk space...")
print(f"Title: {kb_article['title']}")

# Generate embedding
print("\nGenerating embedding...")
response = openai_client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=kb_article['text']
)
embedding = response.data[0].embedding

# Prepare vector for Pinecone
vector = {
    "id": "kb_disk_space_low",
    "values": embedding,
    "metadata": {
        "source": "kb_article",
        "title": kb_article['title'],
        "text": kb_article['text']
    }
}

# Upsert to Pinecone
print("\nUpserting to Pinecone...")
url = f"https://{INDEX_HOST}/vectors/upsert"
payload = {"vectors": [vector]}

response = requests.post(
    url,
    headers={"Api-Key": PINECONE_API_KEY, "Content-Type": "application/json"},
    json=payload,
    verify=False
)

if response.status_code == 200:
    print("✅ SUCCESS! Disk space KB article added to Pinecone")
else:
    print(f"❌ FAILED: {response.status_code}")
    print(response.text)

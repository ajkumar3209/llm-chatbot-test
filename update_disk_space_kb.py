"""
Update disk space KB article to be more concise
"""
import requests
import urllib3
from dotenv import load_dotenv
import os
from openai import OpenAI

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "support-chatbot"
EMBEDDING_MODEL = "text-embedding-3-small"

# Get index host
headers = {
    "Api-Key": PINECONE_API_KEY,
    "Content-Type": "application/json"
}

response = requests.get(
    "https://api.pinecone.io/indexes",
    headers=headers,
    verify=False
)
indexes = response.json()
INDEX_HOST = None
for idx in indexes.get('indexes', []):
    if idx['name'] == INDEX_NAME:
        INDEX_HOST = idx['host']
        break

PINECONE_HEADERS = {
    "Api-Key": PINECONE_API_KEY,
    "Content-Type": "application/json"
}

# Updated KB Article - more concise
kb_article = {
    "title": "How to fix low disk space on server",
    "text": """How to fix low disk space on server

Issue: Disk space low / Disk space full / Disk space showing red

Step 1: Clear temporary files
- Press Win + R, type %temp%, press Enter
- Select all files (Ctrl + A) and delete

Step 2: Clear system temp folder
- Press Win + R, type temp, press Enter
- Select all files (Ctrl + A) and delete

Step 3: Empty Recycle Bin
- Right-click Recycle Bin on desktop
- Click Empty Recycle Bin

Step 4: Remove old files
- Check Downloads, Documents, Desktop folders
- Delete files you don't need

Note: If disk space is still low after these steps, you may need to upgrade. Call support at 1-888-415-5240."""
}

print("="*70)
print("Updating Disk Space KB Article (More Concise)")
print("="*70)

# Generate embedding
print("\nGenerating embedding...")
response = openai_client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=kb_article["text"]
)
embedding = response.data[0].embedding

# Find existing disk space KB article ID
print("\nSearching for existing disk space KB article...")
search_response = requests.post(
    f"https://{INDEX_HOST}/query",
    headers=PINECONE_HEADERS,
    json={
        "vector": embedding,
        "topK": 5,
        "includeMetadata": True,
        "filter": {"source": {"$eq": "kb_article"}}
    },
    verify=False
)

results = search_response.json().get('matches', [])
vector_id = None
for match in results:
    title = match['metadata'].get('title', '')
    if 'disk space' in title.lower():
        vector_id = match['id']
        print(f"Found existing: {title} (ID: {vector_id})")
        break

if not vector_id:
    vector_id = "kb_disk_space_low"
    print(f"Creating new with ID: {vector_id}")

# Prepare vector
vector = {
    "id": vector_id,
    "values": embedding,
    "metadata": {
        "source": "kb_article",
        "title": kb_article["title"],
        "text": kb_article["text"]
    }
}

# Upsert to Pinecone
print(f"\nUpdating in Pinecone...")
upsert_response = requests.post(
    f"https://{INDEX_HOST}/vectors/upsert",
    headers=PINECONE_HEADERS,
    json={"vectors": [vector]},
    verify=False
)

if upsert_response.status_code == 200:
    print("✅ Successfully updated KB article!")
    print(f"\nTitle: {kb_article['title']}")
    print(f"Vector ID: {vector_id}")
else:
    print(f"❌ Failed to update KB article: {upsert_response.status_code}")
    print(upsert_response.text)

print("\n" + "="*70)
print("DONE!")
print("="*70)

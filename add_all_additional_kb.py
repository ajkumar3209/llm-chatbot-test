"""
Process and add ALL KB articles from Additional resolution steps.txt to Pinecone
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
import urllib3
import re

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

# Read the file
with open("SOP and KB Docs/Additional resolution steps.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Split by "Issue :" to get individual KB articles
articles = re.split(r'\n\nIssue\s*:', content)

print(f"Found {len(articles)} KB articles in Additional resolution steps.txt")
print("="*70)

vectors = []
for i, article in enumerate(articles):
    if not article.strip():
        continue
    
    # Extract title (first line)
    lines = article.strip().split('\n')
    if not lines:
        continue
    
    title = lines[0].strip()
    if not title:
        continue
    
    # Full text
    full_text = f"Issue: {article.strip()}"
    
    print(f"\n{i+1}. {title[:60]}...")
    
    # Generate embedding
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=full_text
        )
        embedding = response.data[0].embedding
        
        # Create vector
        vector_id = f"kb_additional_{i}"
        vector = {
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "source": "kb_article",
                "title": f"How to: {title}",
                "text": full_text
            }
        }
        vectors.append(vector)
        print(f"   ✅ Processed")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print("\n" + "="*70)
print(f"Processed {len(vectors)} KB articles")
print("Upserting to Pinecone in batches...")

# Upsert in batches of 100
batch_size = 100
for i in range(0, len(vectors), batch_size):
    batch = vectors[i:i+batch_size]
    
    url = f"https://{INDEX_HOST}/vectors/upsert"
    payload = {"vectors": batch}
    
    response = requests.post(
        url,
        headers={"Api-Key": PINECONE_API_KEY, "Content-Type": "application/json"},
        json=payload,
        verify=False
    )
    
    if response.status_code == 200:
        print(f"✅ Batch {i//batch_size + 1}: Uploaded {len(batch)} vectors")
    else:
        print(f"❌ Batch {i//batch_size + 1} FAILED: {response.status_code}")
        print(response.text)

print("\n" + "="*70)
print("✅ ALL DONE! Additional KB articles are now in Pinecone")
print("="*70)

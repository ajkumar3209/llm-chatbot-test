"""
Update MyPortal KB article to be more concise and user-friendly
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
    "title": "How to reset server password using MyPortal",
    "text": """How to reset server password using MyPortal

Issue: Password reset using MyPortal

MyPortal allows account owners to reset passwords for all users.

Step 1: Contact your account owner to reset your password.

Step 2: Account owner visits myportal.acecloudhosting.com and logs in using Customer ID (CID).

That's it! Your account owner can reset your password from MyPortal.

Note: If you are the account owner and forgot your MyPortal password, click "Forgot Password" on the login page.

Alternative: Call support at 1-888-415-5240 or email support@acecloudhosting.com"""
}

print("="*70)
print("Updating MyPortal KB Article (More Concise)")
print("="*70)

# Generate embedding
print("\nGenerating embedding...")
response = openai_client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=kb_article["text"]
)
embedding = response.data[0].embedding

# Use same vector ID to update
vector_id = "kb_myportal_password_reset"

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

# Upsert to Pinecone (will overwrite existing)
print(f"Updating in Pinecone...")
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
    print(f"\nNew text (more concise):")
    print(kb_article['text'])
else:
    print(f"❌ Failed to update KB article: {upsert_response.status_code}")
    print(upsert_response.text)

print("\n" + "="*70)
print("DONE!")
print("="*70)

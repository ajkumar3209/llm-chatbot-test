"""
Add simplified Selfcare enrollment KB article
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

# Simplified KB Article for Selfcare enrollment
kb_article = {
    "title": "How to enroll in Selfcare Portal",
    "text": """How to enroll in Selfcare Portal

Issue: Selfcare Portal enrollment / registration

Prerequisite: Download Google Authenticator app on your mobile (Play Store or App Store)

Step 1: Go to selfcare.acecloudhosting.com

Step 2: Login with your server credentials
- Username: Myrealdata\\YourUsername
- Password: Your server password

Step 3: Scan the barcode with Google Authenticator app
- Open Google Authenticator app
- Select "Scan barcode"
- Scan the displayed barcode

If barcode doesn't work:
- Click "Can't scan it?" link
- Copy the numbers shown
- In Google Authenticator, select "Manual entry"
- Enter the numbers

Step 4: Enter the one-time code
- Google Authenticator will generate a code
- Enter that code in the "Enter code" field
- Click Next

Step 5: Complete enrollment
- Click "Click Here" at the top of screen
- Choose security questions and provide answers
- Click Next

Done! You're now enrolled in Selfcare Portal.

Note: If you need help with enrollment, call support at 1-888-415-5240."""
}

print("="*70)
print("Adding Selfcare Enrollment KB Article")
print("="*70)

# Generate embedding
print("\nGenerating embedding...")
response = openai_client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=kb_article["text"]
)
embedding = response.data[0].embedding

# Create vector ID
vector_id = "kb_selfcare_enrollment"

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
print(f"Upserting to Pinecone...")
upsert_response = requests.post(
    f"https://{INDEX_HOST}/vectors/upsert",
    headers=PINECONE_HEADERS,
    json={"vectors": [vector]},
    verify=False
)

if upsert_response.status_code == 200:
    print("✅ Successfully added KB article!")
    print(f"\nTitle: {kb_article['title']}")
    print(f"Vector ID: {vector_id}")
else:
    print(f"❌ Failed to add KB article: {upsert_response.status_code}")
    print(upsert_response.text)

# Verify by searching
print("\n" + "="*70)
print("Verifying by searching...")
print("="*70)

test_queries = ["selfcare enrollment", "register selfcare", "enroll selfcare portal"]

for test_query in test_queries:
    print(f"\n--- Query: '{test_query}' ---")
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=test_query
    )
    query_embedding = response.data[0].embedding

    search_response = requests.post(
        f"https://{INDEX_HOST}/query",
        headers=PINECONE_HEADERS,
        json={
            "vector": query_embedding,
            "topK": 2,
            "includeMetadata": True,
            "filter": {"source": {"$eq": "kb_article"}}
        },
        verify=False
    )

    results = search_response.json().get('matches', [])
    for i, match in enumerate(results, 1):
        print(f"{i}. Score: {match['score']:.4f} - {match['metadata'].get('title', 'N/A')}")

print("\n" + "="*70)
print("DONE!")
print("="*70)

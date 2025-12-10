"""
Debug what gets retrieved when user says "shared server" after QuickBooks frozen
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

def get_index_host():
    headers = {
        "Api-Key": PINECONE_API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        "https://api.pinecone.io/indexes",
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    
    indexes = response.json()
    for idx in indexes.get('indexes', []):
        if idx['name'] == INDEX_NAME:
            return idx['host']
    
    raise Exception(f"Index '{INDEX_NAME}' not found")

INDEX_HOST = get_index_host()
PINECONE_HEADERS = {
    "Api-Key": PINECONE_API_KEY,
    "Content-Type": "application/json"
}

def retrieve_context(query: str, top_k: int = 3):
    """Retrieve relevant KB articles from Pinecone."""
    # Expand short queries for better retrieval
    expanded_query = query
    query_lower = query.lower()
    
    # Only expand if it's a QuickBooks-specific query
    if len(query.split()) <= 4:
        # Check if query is about QuickBooks
        qb_keywords = ['quickbooks', 'qb', 'company file', 'lacerte', 'drake', 'proseries']
        if any(keyword in query_lower for keyword in qb_keywords):
            expanded_query = f"How to {query} in QuickBooks"
        else:
            # For non-QB queries, just add "How to"
            expanded_query = f"How to {query}"
    
    print(f"\nOriginal query: {query}")
    print(f"Expanded query: {expanded_query}")
    
    # Generate query embedding
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=expanded_query
    )
    query_embedding = response.data[0].embedding
    
    # Query Pinecone for KB articles only
    url = f"https://{INDEX_HOST}/query"
    payload = {
        "vector": query_embedding,
        "topK": top_k,
        "includeMetadata": True,
        "filter": {"source": {"$eq": "kb_article"}}
    }
    
    response = requests.post(
        url,
        headers=PINECONE_HEADERS,
        json=payload,
        verify=False
    )
    response.raise_for_status()
    results = response.json().get('matches', [])
    
    print(f"\nTop {top_k} results:")
    for i, match in enumerate(results, 1):
        score = match['score']
        title = match['metadata'].get('title', 'No title')
        text_preview = match['metadata'].get('text', '')[:200]
        print(f"\n{i}. Score: {score:.4f}")
        print(f"   Title: {title}")
        print(f"   Text: {text_preview}...")
    
    return results

# Test different queries
print("="*70)
print("TEST 1: User says 'shared server' after QuickBooks frozen")
print("="*70)
retrieve_context("shared server", top_k=3)

print("\n" + "="*70)
print("TEST 2: User says 'dedicated' after QuickBooks frozen")
print("="*70)
retrieve_context("dedicated", top_k=3)

print("\n" + "="*70)
print("TEST 3: Original query 'quickbooks frozen'")
print("="*70)
retrieve_context("quickbooks frozen", top_k=3)

"""
RAG Service for Regulatory Compliance Retrieval using Pinecone and Gemini Embeddings.

This service retrieves relevant regulatory documents (LMA guidelines, EU Taxonomy, SFDR)
to provide compliance context for loan decisions.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests

# Try to import Pinecone
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("[RAG] Warning: Pinecone not installed. RAG features will be disabled.")

# Try to import Google Generative AI for embeddings
try:
    import google.generativeai as genai
    GEMINI_EMBEDDINGS_AVAILABLE = True
except ImportError:
    GEMINI_EMBEDDINGS_AVAILABLE = False
    print("[RAG] Warning: google-generativeai not installed. Using API calls for embeddings.")

# --- MOCK MODE ---
MOCK_MODE = os.getenv("RAG_MOCK_MODE", "false").lower() == "true"


def get_gemini_embedding(text: str, api_key: Optional[str] = None) -> List[float]:
    """
    Generate embedding using Gemini Embeddings API.
    
    Args:
        text: Text to embed
        api_key: Gemini API key (if None, uses GEMINI_API_KEY env var)
    
    Returns:
        List of floats representing the embedding vector
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    # Use Gemini Embeddings API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "models/text-embedding-004",
        "content": {
            "parts": [{
                "text": text
            }]
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "embedding" in result:
            return result["embedding"]["values"]
        else:
            raise RuntimeError("No embedding returned from Gemini API")
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to get embedding from Gemini API: {str(e)}")


def initialize_pinecone() -> Optional[Any]:
    """
    Initialize Pinecone connection and return index.
    
    Returns:
        Pinecone index object or None if unavailable
    """
    if not PINECONE_AVAILABLE:
        return None
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "greenchain-regulations")
    
    if not api_key:
        print("[RAG] Warning: PINECONE_API_KEY not set. RAG features disabled.")
        return None
    
    try:
        pc = Pinecone(api_key=api_key)
        
        # Check if index exists, create if not
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        
        if index_name not in existing_indexes:
            print(f"[RAG] Creating new Pinecone index: {index_name}")
            # IMPORTANT: Gemini text-embedding-004 returns 768-dimensional vectors
            # If you're using a different embedding model, update this dimension accordingly
            # Common dimensions:
            # - Gemini text-embedding-004: 768
            # - OpenAI text-embedding-3-small: 1536
            # - OpenAI text-embedding-3-large: 3072
            # - Cohere embed-english-v3.0: 1024
            pc.create_index(
                name=index_name,
                dimension=768,  # Gemini text-embedding-004 dimension - DO NOT CHANGE unless using different model
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        
        index = pc.Index(index_name)
        print(f"[RAG] Connected to Pinecone index: {index_name}")
        return index
    
    except Exception as e:
        print(f"[RAG] Error initializing Pinecone: {str(e)}")
        return None


def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split document into chunks for embedding.
    
    Args:
        text: Document text
        chunk_size: Maximum characters per chunk
        overlap: Characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


def ingest_regulatory_documents(index: Any, docs_dir: Path) -> int:
    """
    Ingest regulatory documents into Pinecone.
    
    Args:
        index: Pinecone index object
        docs_dir: Directory containing regulatory documents
    
    Returns:
        Number of documents ingested
    """
    if not index:
        return 0
    
    if not docs_dir.exists():
        print(f"[RAG] Warning: Documents directory not found: {docs_dir}")
        return 0
    
    ingested_count = 0
    
    # Process each document file
    for doc_file in docs_dir.glob("*.txt"):
        print(f"[RAG] Processing document: {doc_file.name}")
        
        try:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Chunk the document
            chunks = chunk_document(content)
            
            # Generate embeddings and upsert to Pinecone
            vectors = []
            for i, chunk in enumerate(chunks):
                if MOCK_MODE:
                    # Mock embedding (random vector)
                    embedding = [0.1] * 768
                else:
                    embedding = get_gemini_embedding(chunk)
                
                vectors.append({
                    "id": f"{doc_file.stem}_{i}",
                    "values": embedding,
                    "metadata": {
                        "document": doc_file.stem,
                        "chunk_index": i,
                        "text": chunk[:200]  # Store first 200 chars for reference
                    }
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                index.upsert(vectors=batch)
            
            ingested_count += len(chunks)
            print(f"[RAG] Ingested {len(chunks)} chunks from {doc_file.name}")
        
        except Exception as e:
            print(f"[RAG] Error processing {doc_file.name}: {str(e)}")
    
    return ingested_count


def retrieve_regulatory_context(
    query_text: str,
    index: Optional[Any] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant regulatory context for a query.
    
    Args:
        query_text: Query text (e.g., loan purpose, sustainability factors)
        index: Pinecone index object (if None, will initialize)
        top_k: Number of top results to retrieve
    
    Returns:
        List of relevant document chunks with metadata
    """
    if MOCK_MODE:
        # Return mock regulatory context
        return [
            {
                "text": "LMA Green Lending Guidelines: Loans for sustainable agriculture must demonstrate positive environmental impact through verified practices such as organic farming, water conservation, and biodiversity protection.",
                "document": "lma_guidelines",
                "score": 0.85
            },
            {
                "text": "EU Taxonomy Regulation: Economic activities qualify as environmentally sustainable if they contribute substantially to climate change mitigation or adaptation, do no significant harm to other environmental objectives, and meet minimum safeguards.",
                "document": "eu_taxonomy",
                "score": 0.78
            }
        ]
    
    if not index:
        index = initialize_pinecone()
    
    if not index:
        print("[RAG] Pinecone index not available. Returning empty context.")
        return []
    
    try:
        # Generate query embedding
        query_embedding = get_gemini_embedding(query_text)
        
        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Format results
        context = []
        for match in results.matches:
            context.append({
                "text": match.metadata.get("text", ""),
                "document": match.metadata.get("document", "unknown"),
                "chunk_index": match.metadata.get("chunk_index", 0),
                "score": match.score
            })
        
        return context
    
    except Exception as e:
        print(f"[RAG] Error retrieving context: {str(e)}")
        return []


def format_regulatory_context(context: List[Dict[str, Any]]) -> str:
    """
    Format retrieved regulatory context for LLM prompt.
    
    Args:
        context: List of context dictionaries from retrieve_regulatory_context
    
    Returns:
        Formatted string for LLM prompt
    """
    if not context:
        return ""
    
    formatted = "\n\n=== RELEVANT REGULATORY GUIDELINES ===\n"
    
    for i, item in enumerate(context, 1):
        formatted += f"\n[{i}] Source: {item.get('document', 'Unknown')}\n"
        formatted += f"Relevance Score: {item.get('score', 0):.2f}\n"
        formatted += f"Content: {item.get('text', '')}\n"
    
    formatted += "\n=== END REGULATORY GUIDELINES ===\n"
    
    return formatted


def get_compliance_context(
    loan_purpose: str,
    sustainability_score: float,
    geographic_region: Optional[str] = None,
    index: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Get compliance context for a loan application.
    
    Args:
        loan_purpose: Description of loan purpose
        sustainability_score: Overall sustainability score
        geographic_region: Optional geographic region
        index: Optional Pinecone index (will initialize if None)
    
    Returns:
        Dictionary with compliance context and formatted text
    """
    # Build query from loan purpose and sustainability factors
    query_parts = [loan_purpose] if loan_purpose else []
    
    if sustainability_score >= 70:
        query_parts.append("high sustainability score green lending")
    elif sustainability_score >= 50:
        query_parts.append("moderate sustainability conditional approval")
    else:
        query_parts.append("low sustainability risk assessment")
    
    if geographic_region:
        query_parts.append(f"region {geographic_region}")
    
    query_text = " ".join(query_parts)
    
    # Retrieve context
    context = retrieve_regulatory_context(query_text, index=index)
    
    # Format for LLM
    formatted_context = format_regulatory_context(context)
    
    return {
        "context": context,
        "formatted_context": formatted_context,
        "query": query_text,
        "compliance_score": len(context) > 0  # Simple compliance indicator
    }


# Initialize index on module load (lazy initialization)
_pinecone_index = None

def get_index():
    """Get or initialize Pinecone index."""
    global _pinecone_index
    if _pinecone_index is None:
        _pinecone_index = initialize_pinecone()
    return _pinecone_index

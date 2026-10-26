import re
import math
from typing import List, Dict, Any
from backend.app.review.llm_provider import get_llm_provider

def segment_text(text: str) -> List[str]:
    """
    Splits text into cohesive segments (sentences / phrases).
    """
    raw_segments = re.split(r"(?<=[.!?])\s+|\n+", text)
    cleaned = [s.strip() for s in raw_segments if len(s.strip()) > 3]
    return cleaned if cleaned else [text.strip()]

def tokenize(text: str) -> set:
    words = re.findall(r"\w+", text.lower())
    return set(words)

def keyword_similarity(query_tokens: set, doc_tokens: set) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    intersection = query_tokens.intersection(doc_tokens)
    return len(intersection) / math.sqrt(len(query_tokens) * len(doc_tokens))

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def retrieve_top_k_sources(
    segment: str,
    clauses: List[Dict[str, Any]],
    facts: List[Dict[str, Any]],
    k: int = 5
) -> List[Dict[str, str]]:
    """
    Hybrid Retrieval: combines token keyword matching with vector embeddings.
    Returns top-k grounded source items (clauses and facts).
    """
    provider = get_llm_provider()
    segment_tokens = tokenize(segment)
    segment_vec = provider.get_embedding(segment)

    scored_sources = []

    # 1. Score clauses
    for clause in clauses:
        clause_id = clause["id"]
        clause_text = clause.get("text", "")
        c_tokens = tokenize(clause_text + " " + clause.get("category", "") + " " + clause.get("title", ""))
        kw_score = keyword_similarity(segment_tokens, c_tokens)

        c_vec = provider.get_embedding(clause_text)
        vec_score = cosine_similarity(segment_vec, c_vec)

        # Hybrid weighting (50% keyword, 50% vector)
        hybrid_score = 0.5 * kw_score + 0.5 * max(0.0, vec_score)

        # Boost if explicit keyword matching key policy areas
        if any(term in segment.lower() for term in ["guaranteed", "#1", "best", "cure", "shout", "cheap", "price", "alt", "contrast"]):
            if any(term in clause_text.lower() for term in ["result", "superlative", "cure", "exclamation", "caps", "alt", "contrast"]):
                hybrid_score += 0.3

        scored_sources.append({
            "id": clause_id,
            "type": "clause",
            "text": clause_text,
            "score": hybrid_score
        })

    # 2. Score facts
    for fact in facts:
        fact_id = fact["id"]
        fact_text = f"Approved fact {fact_id}: {fact.get('label', '')} is {fact.get('value', '')} (source: {fact.get('source', '')})"
        f_tokens = tokenize(fact_text)
        kw_score = keyword_similarity(segment_tokens, f_tokens)

        f_vec = provider.get_embedding(fact_text)
        vec_score = cosine_similarity(segment_vec, f_vec)

        hybrid_score = 0.5 * kw_score + 0.5 * max(0.0, vec_score)

        if "price" in segment.lower() or "rs" in segment.lower() or "₹" in segment.lower():
            if "price" in fact.get("label", "").lower():
                hybrid_score += 0.4

        scored_sources.append({
            "id": fact_id,
            "type": "fact",
            "text": fact_text,
            "score": hybrid_score
        })

    # Sort descending by hybrid relevance score
    scored_sources.sort(key=lambda s: s["score"], reverse=True)
    return scored_sources[:k]

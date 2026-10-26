import abc
import json
import hashlib
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.core.config import settings

class AIJudgeFinding(BaseModel):
    issue: str
    category: str  # 'Unsupported claim' | 'Tone' | 'Voice' | 'Factual accuracy'
    quoted_text: str
    source_id: str
    explanation: str
    suggested_fix: Optional[str] = None
    confidence: str = "high"  # 'high' | 'medium' | 'low'

class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate_judge_findings(self, segment: str, retrieved_sources: List[Dict[str, str]]) -> List[AIJudgeFinding]:
        pass

    @abc.abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        pass

class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM Provider for offline testing, CI/CD, and fast evaluation.
    Provides deterministic judgements matching the grounded retrieved sources.
    """
    def generate_judge_findings(self, segment: str, retrieved_sources: List[Dict[str, str]]) -> List[AIJudgeFinding]:
        findings = []
        retrieved_ids = {s["id"] for s in retrieved_sources}

        # Check for tone/voice nuances if R-02 or R-03 are retrieved
        if "R-03" in retrieved_ids and ("BUY NOW" in segment or "LOVE" in segment):
            findings.append(AIJudgeFinding(
                issue="Aggressive call-to-action capitalized",
                category="Tone",
                quoted_text="BUY NOW",
                source_id="R-03",
                explanation="Promotional shouting detected in call to action.",
                suggested_fix="Shop now",
                confidence="high"
            ))

        # Check for claim nuance if C-01 is retrieved
        if "C-01" in retrieved_ids and "100% guaranteed" in segment.lower():
            findings.append(AIJudgeFinding(
                issue="Absolute efficacy guarantee",
                category="Unsupported claim",
                quoted_text="100% guaranteed results",
                source_id="C-01",
                explanation="Cosmetic products cannot guarantee 100% clinical efficacy without peer-reviewed double-blind trial evidence.",
                suggested_fix="clinically demonstrated results",
                confidence="high"
            ))

        return findings

    def get_embedding(self, text: str) -> List[float]:
        # Fast deterministic hash-based 64-dimensional pseudo-embedding
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Create normalized floats between -1.0 and 1.0
        vec = [(b / 127.5) - 1.0 for b in h[:64]]
        return vec

class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Provider using official google-genai SDK.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GeminiProvider] Init warning: {e}")

    def generate_judge_findings(self, segment: str, retrieved_sources: List[Dict[str, str]]) -> List[AIJudgeFinding]:
        if not self.client:
            return MockLLMProvider().generate_judge_findings(segment, retrieved_sources)

        system_prompt = (
            "You are BrandLens AI Judge, an uncompromising brand-governance engine.\n"
            "CRITICAL RULES (NON-NEGOTIABLE):\n"
            "1. 'Evidence or silence': You MUST ONLY cite source IDs provided in the RETRIEVED SOURCES list.\n"
            "2. NEVER invent guideline rules, policy clauses, or unmentioned facts.\n"
            "3. The 'quoted_text' MUST be an EXACT VERBATIM substring of the input content segment.\n"
            "4. Output MUST be valid JSON adhering strictly to the schema: an array of objects with keys: "
            "issue, category, quoted_text, source_id, explanation, suggested_fix, confidence ('high'|'medium'|'low').\n"
            "If no issues violate the retrieved sources, return an empty array []."
        )

        sources_formatted = "\n".join([f"[{s['id']}] {s['text']}" for s in retrieved_sources])
        user_prompt = f"RETRIEVED SOURCES:\n{sources_formatted}\n\nCONTENT SEGMENT TO EVALUATE:\n\"{segment}\""

        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[system_prompt, user_prompt],
                    config={"response_mime_type": "application/json"}
                )
                raw_text = response.text.strip()
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict) and "findings" in parsed:
                    parsed = parsed["findings"]
                if not isinstance(parsed, list):
                    parsed = [parsed]
                
                results = [AIJudgeFinding(**item) for item in parsed]
                return results
            except Exception as e:
                if attempt == 1:
                    print(f"[GeminiProvider] Parse failure after retry: {e}")
                    return []
        return []

    def get_embedding(self, text: str) -> List[float]:
        # Fallback to local pseudo-embedding or Gemini embedding model
        return MockLLMProvider().get_embedding(text)

def get_llm_provider() -> BaseLLMProvider:
    provider_name = settings.LLM_PROVIDER.lower()
    if provider_name == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider()
    return MockLLMProvider()

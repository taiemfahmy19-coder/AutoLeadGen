"""AutoLeadGen V3 — Local AI Lead Intelligence Service.

100% Free / Local Stack:
- Scikit-learn TF-IDF + Naive Bayes / Nearest Neighbors for industry classification & semantic dedup
- Heuristic + extractive text summarization
- Data completeness scoring
- Optional Ollama integration (gracefully bypassed if Ollama not running)
"""
import re
import logging
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("AutoLeadGen")

# Industry training corpus for zero-shot / few-shot local classifier
INDUSTRY_SEEDS = {
    "Technology & Software": "software development web app cloud saas ai data tech digital platform it solutions cybersecurity code programming",
    "Healthcare & Medical": "clinic doctor hospital dental pharmacy medical health medicine clinic surgery care wellness patient therapy",
    "Restaurants & Food": "restaurant cafe coffee food dining bakery grill burger pizza delivery catering bar kitchen bistro",
    "Real Estate & Construction": "real estate properties architecture construction building contractor apartments villas broker development interior design",
    "Retail & E-commerce": "shop store boutique supermarket clothes fashion shoes electronics retail cosmetics products market jewelry",
    "Professional Services": "consulting legal law accounting legal finance audit advisory insurance marketing agency hr recruitment",
    "Automotive": "cars auto repair mechanics car wash rental vehicles dealership spare parts tires automotive garage",
    "Education & Training": "school academy university courses training institute education learning college students tutoring",
    "Tourism & Hospitality": "hotel travel resort tourism flights holidays booking vacation hostel suites guest house",
    "Manufacturing & Industrial": "factory industrial manufacturing machinery packaging processing supply warehouse distribution steel plastics",
}


class AILeadIntelligence:
    def __init__(self):
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self._industries = list(INDUSTRY_SEEDS.keys())
        self._industry_corpus = [INDUSTRY_SEEDS[k] for k in self._industries]
        try:
            self._tfidf_matrix = self._vectorizer.fit_transform(self._industry_corpus)
        except Exception as e:
            logger.warning(f"TF-IDF fit error: {e}")
            self._tfidf_matrix = None

    def classify_industry(self, business_name: str, website_text: str = "", default: str = "Business") -> str:
        """Classify business industry using local TF-IDF cosine similarity."""
        combined = f"{business_name} {website_text}".lower().strip()
        if not combined or self._tfidf_matrix is None:
            return default
        try:
            vec = self._vectorizer.transform([combined])
            sims = cosine_similarity(vec, self._tfidf_matrix)[0]
            best_idx = int(np.argmax(sims))
            if sims[best_idx] > 0.05:
                return self._industries[best_idx]
            return default
        except Exception as e:
            logger.debug(f"AI industry classification error: {e}")
            return default

    def score_data_completeness(self, lead: Dict[str, Any]) -> float:
        """
        Calculate data completeness score from 0.0 to 1.0.
        Weighted criteria:
        - phone: 0.25
        - email: 0.25
        - website: 0.15
        - coordinates (lat/lon): 0.15
        - address/city: 0.10
        - business_name: 0.10
        """
        score = 0.0
        if lead.get("business_name") and len(str(lead["business_name"]).strip()) >= 2:
            score += 0.10
        if lead.get("phone") and len(str(lead["phone"]).strip()) >= 7:
            score += 0.25
        if lead.get("email") and "@" in str(lead["email"]):
            score += 0.25
        if lead.get("website") and len(str(lead["website"]).strip()) >= 5:
            score += 0.15
        if lead.get("latitude") is not None and lead.get("longitude") is not None:
            score += 0.15
        if lead.get("address") or lead.get("city"):
            score += 0.10
        return round(min(1.0, score), 2)

    def summarize_business(self, website_text: str, max_words: int = 40) -> str:
        """Generate concise extractive summary without requiring heavy external LLMs."""
        if not website_text or len(website_text.strip()) < 10:
            return ""
        # Clean text
        clean = re.sub(r"\s+", " ", website_text).strip()
        sentences = re.split(r"(?<=[.!?]) +", clean)
        summary_sentences = []
        word_count = 0
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 20 and not re.search(r"cookie|privacy|copyright|all rights reserved|terms", s_clean, re.I):
                words = len(s_clean.split())
                if word_count + words <= max_words:
                    summary_sentences.append(s_clean)
                    word_count += words
                else:
                    break
        if not summary_sentences and sentences:
            summary_sentences = [sentences[0][:150]]
        return " ".join(summary_sentences)

    def detect_semantic_duplicates(self, candidates: List[Dict[str, Any]], threshold: float = 0.85) -> List[Tuple[int, int, float]]:
        """
        Detect pairs of leads that are likely duplicates based on semantic text vectorization.
        Returns list of (lead_id_1, lead_id_2, similarity_score).
        """
        if len(candidates) < 2:
            return []
        texts = [
            f"{c.get('business_name', '')} {c.get('city', '')} {c.get('address', '')}".lower().strip()
            for c in candidates
        ]
        try:
            vec = TfidfVectorizer(ngram_range=(1, 2)).fit_transform(texts)
            sim_matrix = cosine_similarity(vec)
            duplicates = []
            n = len(candidates)
            for i in range(n):
                for j in range(i + 1, n):
                    sim = float(sim_matrix[i, j])
                    if sim >= threshold:
                        id1 = candidates[i].get("id", i)
                        id2 = candidates[j].get("id", j)
                        duplicates.append((id1, id2, round(sim, 2)))
            return duplicates
        except Exception as e:
            logger.debug(f"Semantic dedup error: {e}")
            return []


# Global singleton
ai_service = AILeadIntelligence()

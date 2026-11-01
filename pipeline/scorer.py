"""AutoLeadGen v2 - Pipeline Scorer: Multi-Factor Objective Lead Scoring Engine (0 - 100 Points)."""
from pipeline.cleaner import normalize_phone, is_mobile_phone, clean_website
from config.constants import (
    SCORING_WEIGHTS,
    HIGH_FIT_AI_INDUSTRIES,
    WA_STATUS_VERIFIED,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
)
from core.models import LeadScoreBreakdown


def calculate_industry_fit(industry: str, product_description: str = "") -> int:
    """Calculate Industry/Niche Clarity score (0 - 10 points)."""
    combined = f"{industry} {product_description}".lower().strip()
    if not combined:
        return 0

    for keyword, score in HIGH_FIT_AI_INDUSTRIES.items():
        if keyword in combined:
            return score

    if len(combined) >= 4:
        return 4
    return 0


def calculate_ai_fit(industry: str, product_description: str = "") -> int:
    """Legacy compatibility helper."""
    ind = f"{industry} {product_description}".lower().strip()
    if any(k in ind for k in ["عطور", "شوكولاتة", "ملابس", "perfume", "مطاعم"]):
        return 25
    if any(k in ind for k in ["أثاث", "ديكور", "إلكترونيات"]):
        return 20
    if any(k in ind for k in ["مدرس", "برمجة", "تصميم"]):
        return 15
    return 5


def calculate_priority(score: int, past_status: str = None) -> str:
    """
    Classify leads into High, Medium, or Low Priority.
    Rules:
    - High Priority: Score >= 80, not previously contacted
    - Medium Priority: 50 <= Score < 80
    - Low Priority: Score < 50 or marked DO_NOT_CONTACT/INVALID
    """
    if past_status in ["DO_NOT_CONTACT", "INVALID"]:
        return PRIORITY_LOW
    if score >= 80:
        return PRIORITY_HIGH
    if score >= 50:
        return PRIORITY_MEDIUM
    return PRIORITY_LOW


def calculate_score(
    phone: str = "",
    website: str = "",
    business_name: str = "",
    address: str = "",
    industry: str = "",
    whatsapp_status: str = "UNKNOWN",
    source: str = "",
    product_description: str = "",
    *args,
    **kwargs,
) -> tuple[int, dict]:
    """
    Calculate an objective, multi-factor lead score from 0 to 100.
    
    Weights Breakdown:
    - Phone Valid:       +20
    - Mobile Carrier:    +15
    - WhatsApp Verified: +25 (Only given when verified!)
    - Business Name:     +10
    - Address Complete:  +10
    - Category/Industry: +10
    - Digital/Source:    +10
    Total Max: 100
    
    Returns: (total_score: int, breakdown: dict)
    """
    breakdown = LeadScoreBreakdown()

    # 1. Phone Valid (20 pts)
    norm_phone = normalize_phone(phone)
    if norm_phone and len(norm_phone) >= 10:
        breakdown.phone_valid = SCORING_WEIGHTS.get("phone_valid", 20)

    # 2. Mobile Carrier (15 pts) - strictly mobile capable of WhatsApp
    if is_mobile_phone(norm_phone):
        breakdown.mobile_carrier = SCORING_WEIGHTS.get("mobile_carrier", 15)

    # 3. WhatsApp Verified (25 pts) - ONLY if verified
    if whatsapp_status == WA_STATUS_VERIFIED:
        breakdown.whatsapp_verified = SCORING_WEIGHTS.get("whatsapp_verified", 25)

    # 4. Business Name Complete (10 pts)
    if business_name and len(business_name.strip()) >= 2:
        breakdown.business_name = SCORING_WEIGHTS.get("business_name", 10)

    # 5. Address Complete (10 pts)
    if address and len(address.strip()) >= 3:
        breakdown.address = SCORING_WEIGHTS.get("address", 10)

    # 6. Industry Clarity (10 pts)
    breakdown.industry_clarity = calculate_industry_fit(industry, product_description)

    # 7. Source & Digital Presence Quality (10 pts)
    if source in ["curated_seed", "verified_directory", "manual", "official"]:
        breakdown.source_quality = SCORING_WEIGHTS.get("source_quality", 10)
    elif source in ["search", "google_maps"]:
        breakdown.source_quality = 5
    elif clean_website(website):
        breakdown.source_quality = 10
    else:
        breakdown.source_quality = 0

    total = (
        breakdown.phone_valid
        + breakdown.mobile_carrier
        + breakdown.whatsapp_verified
        + breakdown.business_name
        + breakdown.address
        + breakdown.industry_clarity
        + breakdown.source_quality
    )
    breakdown.total = max(0, min(100, total))

    b_dict = breakdown.to_dict()
    b_dict["priority"] = calculate_priority(breakdown.total)

    return breakdown.total, b_dict

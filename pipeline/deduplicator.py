"""AutoLeadGen v2 - Pipeline Deduplicator: Indexed SQL-First Deduplication and Safe Merging."""
import re
from difflib import SequenceMatcher
from pipeline.cleaner import normalize_phone, clean_website, clean_business_name, clean_address
from config.constants import WA_STATUS_VERIFIED, WA_STATUS_UNKNOWN


def calculate_similarity(str1: str, str2: str) -> int:
    """
    Calculate similarity between two strings from 0 to 100.
    Combines word token overlap and character sequence matching.
    """
    if not str1 or not str2:
        return 0

    s1 = " ".join(str(str1).lower().split())
    s2 = " ".join(str(str2).lower().split())

    if s1 == s2:
        return 100

    tokens1 = set(s1.split())
    tokens2 = set(s2.split())
    if not tokens1 or not tokens2:
        return 0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    if not intersection:
        return 0

    token_ratio = (len(intersection) / len(union)) * 100
    seq_ratio = SequenceMatcher(None, s1, s2).ratio() * 100

    return int(round((seq_ratio * 0.5) + (token_ratio * 0.5)))


def normalize_url_domain(url: str) -> str:
    """Extract and normalize domain from URL for comparison."""
    if not url:
        return ""
    cleaned = clean_website(url).lower()
    cleaned = re.sub(r"^https?://", "", cleaned)
    cleaned = re.sub(r"^www\.", "", cleaned)
    return cleaned.split("/")[0].strip()


class Deduplicator:
    def __init__(self, db):
        self.db = db

    def is_duplicate(self, business_name: str, phone: str, address: str = "", website: str = "", source: str = "search"):
        """
        Check if a prospective lead matches an existing lead in the database.
        Returns: (is_dup: bool, existing_lead_id: int or None)
        """
        status, reason, lead_id = self.evaluate_duplicate(business_name, phone, address, website, source=source)
        return (lead_id is not None), lead_id

    def get_duplicate_status(self, business_name: str, phone: str, address: str = "", website: str = "", source: str = "search"):
        """Return user-friendly duplicate status label and reason code."""
        status, reason, _ = self.evaluate_duplicate(business_name, phone, address, website, source=source)
        return status, reason

    def evaluate_duplicate(self, business_name: str, phone: str, address: str = "", website: str = "", source: str = "search"):
        """
        Check duplicate status using 5-level strict deduplication:
        Level 1 (Phone): Fast indexed search on normalized E.164 and digits-only phone.
        Level 2 (Website/Domain): Fast indexed search on normalized URL domain.
        Level 3 (Business Name): Token & sequence similarity (>= 65%) with matching city/address, or high-confidence name match (>= 85%).
        Level 4 (Place/Listing): Matching Google Maps place URL or listing identifier.
        Level 5 (Cross-Source): Identify existing lead even if coming from a different source.

        Returns: (status_label: str, reason_key: str, matching_lead_id: int or None)
        """
        normalized_phone = normalize_phone(phone)
        domain = normalize_url_domain(website)
        name_clean = clean_business_name(business_name)
        addr_clean = clean_address(address)
        phone_digits = "".join(filter(str.isdigit, str(phone or "")))

        # 1. Level 1: Fast Indexed Search on Phone
        if normalized_phone and hasattr(self.db, "get_lead_by_phone"):
            match = self.db.get_lead_by_phone(normalized_phone)
            if match:
                match_src = match[7] if len(match) > 7 else "unknown"
                reason = "cross_source_phone" if (source and match_src and source != match_src) else "phone_normalized"
                return "Duplicate (Same Phone Normalized)", reason, match[0]

        # 2. Level 2: Fast Indexed Search on Website Domain
        if domain and hasattr(self.db, "get_lead_by_website"):
            match = self.db.get_lead_by_website(domain)
            if match:
                return "Duplicate (Same Website)", "website", match[0]

        # Fallback to in-memory check for MockDB or Levels 3, 4, 5 check
        existing_leads = self.db.get_all_leads() if hasattr(self.db, "get_all_leads") else []
        for lead in existing_leads:
            ex_id = lead[0]
            ex_name = lead[1] or ""
            ex_phone = lead[2] or ""
            ex_addr = lead[3] or ""
            ex_site = lead[4] or ""
            ex_src = lead[7] if len(lead) > 7 else ""

            ex_norm_phone = normalize_phone(ex_phone)
            ex_domain = normalize_url_domain(ex_site)

            # Level 1 in memory fallback
            if normalized_phone and ex_norm_phone and normalized_phone == ex_norm_phone:
                reason = "cross_source_phone" if (source and ex_src and source != ex_src) else "phone_normalized"
                return "Duplicate (Same Phone Normalized)", reason, ex_id

            # Level 2 in memory fallback (Website domain)
            if domain and ex_domain and domain == ex_domain:
                return "Duplicate (Same Website)", "website", ex_id

            # Level 4: Place / Listing URL match (Google Maps place identifier or maps link)
            if website and ex_site and ("maps.google" in website or "google.com/maps" in website) and ex_site == website:
                return "Duplicate (Same Place Listing)", "place_listing_url", ex_id

            # Level 3: Same Business Name + City/Address (Both must match >= 60% to protect distinct branches)
            if name_clean and ex_name and addr_clean and ex_addr:
                name_sim = calculate_similarity(name_clean, ex_name)
                if name_sim >= 60:
                    addr_sim = calculate_similarity(addr_clean, ex_addr)
                    if addr_sim >= 60:
                        reason = "cross_source_name" if (source and ex_src and source != ex_src) else "name_address"
                        return "Duplicate (Same Name + Address)", reason, ex_id

        return "Unique", "", None

    def merge_if_duplicate(
        self,
        business_name: str,
        phone: str,
        address: str = "",
        website: str = "",
        industry: str = "",
        city: str = "",
        score: int = 0,
        whatsapp_status: str = WA_STATUS_UNKNOWN,
        source: str = "search",
        language: str = "Arabic",
    ):
        """
        Atomic merge or insert:
        - If duplicate: fills missing master fields and records in merge_history.
        - If unique: inserts new lead.
        
        Returns: (lead_id: int, was_merged: bool, reason: str)
        """
        is_dup, master_id = self.is_duplicate(business_name, phone, address, website)

        if is_dup and master_id:
            master = self.db.get_lead_by_id(master_id)
            if not master:
                new_id = self.db.insert_lead(
                    business_name=business_name,
                    phone=normalize_phone(phone),
                    address=clean_address(address),
                    website=clean_website(website),
                    industry=industry,
                    city=city,
                    source=source,
                    score=score,
                    whatsapp_status=whatsapp_status,
                )
                return new_id, False, ""

            updates = {}
            if not master[2] and phone:
                updates["phone"] = normalize_phone(phone)
            if not master[3] and address:
                updates["address"] = clean_address(address)
            if not master[4] and website:
                updates["website"] = clean_website(website)
            if not master[5] and industry:
                updates["industry"] = industry
            if not master[6] and city:
                updates["city"] = city

            new_score = max(score, (master[8] or 0))
            if new_score > (master[8] or 0):
                updates["score"] = new_score

            master_wa = master[13] if len(master) > 13 else WA_STATUS_UNKNOWN
            if whatsapp_status == WA_STATUS_VERIFIED and master_wa != WA_STATUS_VERIFIED:
                updates["whatsapp_status"] = WA_STATUS_VERIFIED

            if updates:
                self.db.update_lead_fields(master_id, **updates)

            _, reason, _ = self.evaluate_duplicate(business_name, phone, address, website)
            self.db.insert_merge_history(
                lead_id=master_id,
                source_lead_id=None,
                reason=f"Inline merge on import: {reason}",
                master_record_id=master_id,
            )
            return master_id, True, reason

        else:
            new_id = self.db.insert_lead(
                business_name=business_name,
                phone=normalize_phone(phone),
                address=clean_address(address),
                website=clean_website(website),
                industry=industry,
                city=city,
                source=source,
                score=score,
                whatsapp_status=whatsapp_status,
                language=language,
            )
            return new_id, False, ""

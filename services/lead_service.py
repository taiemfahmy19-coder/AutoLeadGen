"""AutoLeadGen v2 - Services: Lead Processing and Pipeline Orchestration."""
from pipeline.cleaner import clean_data, normalize_phone, is_mobile_phone, get_phone_validity
from pipeline.scorer import calculate_score
from pipeline.deduplicator import Deduplicator
from database.repository import LeadRepository
from config.constants import (
    STATUS_NEW,
    STATUS_QUALIFIED,
    WA_STATUS_UNKNOWN,
    SCORE_QUALIFIED_THRESHOLD,
)
from utils.logger import info, audit


class LeadService:
    def __init__(self, db: LeadRepository):
        self.db = db
        self.deduplicator = Deduplicator(self.db)

    def process_and_save_lead(
        self,
        business_name: str,
        phone: str,
        address: str = "",
        website: str = "",
        industry: str = "",
        city: str = "",
        source: str = "search",
        whatsapp_status: str = WA_STATUS_UNKNOWN,
        country: str = "",
        language: str = None,
    ) -> dict:
        """
        Clean, score, deduplicate, and persist a single lead record.
        """
        # 1. Clean & Validate
        cleaned = clean_data(
            business_name=business_name,
            phone=phone,
            address=address,
            website=website,
            industry=industry,
            city=city,
            whatsapp_status=whatsapp_status,
            country=country,
            language=language,
        )

        # 2. Score objectively
        score, breakdown = calculate_score(
            phone=cleaned["phone"],
            website=cleaned["website"],
            business_name=cleaned["business_name"],
            address=cleaned["address"],
            industry=cleaned["industry"],
            whatsapp_status=cleaned["whatsapp_status"],
            source=source,
        )

        # 3. Safe Atomic Deduplication
        lead_id, was_merged, reason = self.deduplicator.merge_if_duplicate(
            business_name=cleaned["business_name"],
            phone=cleaned["phone"],
            address=cleaned["address"],
            website=cleaned["website"],
            industry=cleaned["industry"],
            city=cleaned["city"],
            score=score,
            whatsapp_status=cleaned["whatsapp_status"],
            source=source,
            language=cleaned["language"],
        )

        # 4. Auto-qualify if score threshold reached and has valid mobile
        if not was_merged and score >= SCORE_QUALIFIED_THRESHOLD and is_mobile_phone(cleaned["phone"]):
            self.db.update_lead_status(lead_id, STATUS_QUALIFIED)

        return {
            "lead_id": lead_id,
            "was_merged": was_merged,
            "reason": reason,
            "cleaned": cleaned,
            "score": score,
            "breakdown": breakdown,
        }

    def import_raw_pasted_lines(self, raw_text: str, default_city: str = "القاهرة", default_industry: str = "عام") -> int:
        """
        Process user pasted lines (e.g. '01012345678, محل كذا, القاهرة').
        Never assumes VERIFIED status blindly!
        """
        if not raw_text or not raw_text.strip():
            return 0

        lines = raw_text.strip().split("\n")
        added_count = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(",")]
            raw_phone = parts[0]
            b_name = parts[1] if len(parts) > 1 and parts[1] else f"عميل {raw_phone[-4:]}"
            c_city = parts[2] if len(parts) > 2 and parts[2] else default_city
            c_ind = parts[3] if len(parts) > 3 and parts[3] else default_industry

            res = self.process_and_save_lead(
                business_name=b_name,
                phone=raw_phone,
                address=c_city,
                website="",
                industry=c_ind,
                city=c_city,
                source="manual_import",
                whatsapp_status=WA_STATUS_UNKNOWN,  # Must be UNKNOWN until verified!
            )
            added_count += 1

        info(f"LeadService: Imported {added_count} raw leads from text input.")
        return added_count

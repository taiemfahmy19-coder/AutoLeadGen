import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.constants import detect_country_and_language, MULTILINGUAL_TEMPLATES
from integrations.maps_scraper import LeadScraper
from database.repository import LeadRepository
from services.lead_service import LeadService
from services.outreach_service import OutreachService


class TestSearchMultilingualAndDedup(unittest.TestCase):

    def test_americas_language_is_always_english(self):
        """Rule: Any lead from the Americas must be assigned English."""
        cases = [
            ("الولايات المتحدة (USA)", "+13055551234"),
            ("كندا", "+14165551234"),
            ("المكسيك", "+525512345678"),
            ("البرازيل", "+5511999998888"),
            ("الأرجنتين", "+541112345678"),
            ("كولومبيا", "+573001234567"),
        ]
        for country, phone in cases:
            res = detect_country_and_language(phone=phone, country_name=country)
            self.assertEqual(
                res["language"],
                "English",
                f"Failed for {country} ({phone}): expected English, got {res['language']}"
            )
            self.assertEqual(res["region"], "Americas")

    def test_arab_countries_language_is_arabic(self):
        """Rule: Any lead from an Arab country must be assigned Arabic."""
        cases = [
            ("مصر", "+201012345678"),
            ("المملكة العربية السعودية", "+966501234567"),
            ("الإمارات العربية المتحدة", "+971501234567"),
            ("الكويت", "+96550123456"),
            ("قطر", "+97433123456"),
            ("الأردن", "+962791234567"),
            ("المغرب", "+212612345678"),
        ]
        for country, phone in cases:
            res = detect_country_and_language(phone=phone, country_name=country)
            self.assertEqual(
                res["language"],
                "Arabic",
                f"Failed for {country} ({phone}): expected Arabic, got {res['language']}"
            )
            self.assertEqual(res["region"], "MENA")

    def test_other_countries_language(self):
        """Rule: Any country outside the Arab world strictly receives English (no German, French, Spanish, etc.)."""
        # France -> English
        fr = detect_country_and_language(phone="+33612345678", country_name="فرنسا")
        self.assertEqual(fr["language"], "English")

        # Germany -> English
        de = detect_country_and_language(phone="+491512345678", country_name="ألمانيا")
        self.assertEqual(de["language"], "English")

        # Spain -> English
        es = detect_country_and_language(phone="+34612345678", country_name="إسبانيا")
        self.assertEqual(es["language"], "English")

        # Turkey -> English
        tr = detect_country_and_language(phone="+905321234567", country_name="تركيا")
        self.assertEqual(tr["language"], "English")

        # UK -> English
        uk = detect_country_and_language(phone="+447911123456", country_name="المملكة المتحدة (UK)")
        self.assertEqual(uk["language"], "English")

        # Australia -> English
        au = detect_country_and_language(phone="+61412345678", country_name="أستراليا")
        self.assertEqual(au["language"], "English")

    def test_hard_limit_max_50(self):
        """Verify that searches strictly cap results to a maximum of 50."""
        scraper = LeadScraper(headless=True)
        res = scraper.search_leads(
            industry="عطور",
            city="القاهرة",
            country="مصر",
            country_code="20",
            limit=100,
            use_live_browser=False
        )
        self.assertLessEqual(len(res), 50, f"Results exceeded 50: got {len(res)}")

    def test_strict_deduplication_excludes_previous_leads(self):
        """Verify that any lead in exclude_phones is NEVER returned in search results."""
        scraper = LeadScraper(headless=True)
        seed_phone_to_exclude = "+201002345671"
        res = scraper.search_leads(
            industry="عطور",
            city="القاهرة",
            country="مصر",
            country_code="20",
            limit=10,
            use_live_browser=False,
            exclude_phones={seed_phone_to_exclude}
        )
        returned_phones = [r["phone"] for r in res]
        self.assertNotIn(
            seed_phone_to_exclude,
            returned_phones,
            f"Seed phone {seed_phone_to_exclude} was returned despite being in exclude_phones!"
        )

    def test_personalized_message_generation_by_language(self):
        """Verify personalized message building with Spintax for Arabic and English."""
        # Arabic
        ar_geo = detect_country_and_language(phone="+201012345678", country_name="مصر")
        ar_msg = OutreachService.build_personalized_message(
            ar_geo["template"],
            business="قصر العطور",
            industry="عطور",
            city="القاهرة"
        )
        self.assertIn("قصر العطور", ar_msg)
        self.assertNotIn("{business}", ar_msg)

        # English (Americas)
        us_geo = detect_country_and_language(phone="+13055551234", country_name="USA")
        en_msg = OutreachService.build_personalized_message(
            us_geo["template"],
            business="Miami Fragrance",
            industry="Perfumes",
            city="Miami"
        )
        self.assertIn("Miami Fragrance", en_msg)
        self.assertNotIn("{business}", en_msg)
        self.assertIn("Miami", en_msg)


if __name__ == "__main__":
    unittest.main()

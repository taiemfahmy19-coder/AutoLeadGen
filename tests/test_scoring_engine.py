"""AutoLeadGen v2 - Comprehensive Unit Tests: Objective Lead Scoring Engine."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.scorer import calculate_score, calculate_industry_fit
from config.constants import WA_STATUS_VERIFIED, WA_STATUS_UNKNOWN


class TestScoringEngine(unittest.TestCase):

    def test_complete_verified_lead_score(self):
        # Phone: +20, Mobile: +15, WA Verified: +25, Name: +10, Addr: +10, Industry: +10, Source: +10 = 100
        score, breakdown = calculate_score(
            phone="01012345678",
            website="https://royal-perfumes.com",
            business_name="قصر العطور الملكي",
            address="شارع شهاب، المهندسين",
            industry="عطور وبرفانات",
            whatsapp_status=WA_STATUS_VERIFIED,
            source="curated_seed"
        )
        self.assertEqual(score, 100)
        self.assertEqual(breakdown["phone_valid"], 20)
        self.assertEqual(breakdown["mobile_carrier"], 15)
        self.assertEqual(breakdown["whatsapp_verified"], 25)
        self.assertEqual(breakdown["business_name"], 10)
        self.assertEqual(breakdown["address"], 10)
        self.assertEqual(breakdown["industry_clarity"], 10)
        self.assertEqual(breakdown["source_quality"], 10)

    def test_unverified_lead_does_not_get_whatsapp_points(self):
        score, breakdown = calculate_score(
            phone="01012345678",
            website="https://royal-perfumes.com",
            business_name="قصر العطور الملكي",
            address="شارع شهاب، المهندسين",
            industry="عطور",
            whatsapp_status=WA_STATUS_UNKNOWN,
            source="search"
        )
        # 20 + 15 + 0 (WA) + 10 + 10 + 10 + 5 = 70
        self.assertEqual(breakdown["whatsapp_verified"], 0)
        self.assertEqual(score, 70)

    def test_no_score_inflation_for_generic_word_mahal(self):
        """
        REGRESSION TEST:
        Generic word 'محل' (shop) MUST NOT automatically award 20 or 25 points!
        """
        # A non-fit domain like tires/plumbing with word 'محل'
        fit_score = calculate_industry_fit("محل تصليح كاوتش")
        self.assertLessEqual(fit_score, 4)

    def test_landline_loses_mobile_points(self):
        score, breakdown = calculate_score(
            phone="0233445566",  # Cairo landline
            business_name="محل تجاري",
            industry="عام"
        )
        self.assertEqual(breakdown["phone_valid"], 20)
        self.assertEqual(breakdown["mobile_carrier"], 0)


if __name__ == "__main__":
    unittest.main()

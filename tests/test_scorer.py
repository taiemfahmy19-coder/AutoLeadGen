"""Lead Scoring Engine Unit Tests."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.scorer import calculate_score, calculate_industry_fit, calculate_ai_fit


class TestScorer(unittest.TestCase):

    def test_complete_perfume_shop_score(self):
        # AutoLeadGen v2 Objective Scoring:
        # Phone: ✓ (20)
        # Mobile Carrier: ✓ (15)
        # Business Name: ✓ (10)
        # Address: ✓ (10)
        # Category Clarity: ✓ (10)
        # Source Quality: ✓ (10)
        # Expected Unverified Score = 75
        score, breakdown = calculate_score(
            phone="01012345678",
            website="https://ahmedperfumes.com",
            business_name="محل أحمد للعطور",
            address="شارع عباس العقاد، مدينة نصر، القاهرة",
            industry="عطور",
            product_description="برفانات فرنسية وشرقية"
        )
        self.assertEqual(score, 75)
        self.assertEqual(breakdown["phone_valid"], 20)
        self.assertEqual(breakdown["mobile_carrier"], 15)
        self.assertEqual(breakdown["business_name"], 10)
        self.assertEqual(breakdown["address"], 10)
        self.assertEqual(breakdown["industry_clarity"], 10)
        self.assertEqual(breakdown["source_quality"], 10)

    def test_incomplete_lead_score(self):
        # Incomplete lead: missing website, missing address
        score, breakdown = calculate_score(
            phone="01012345678",
            website="",
            business_name="محل",
            address="",
            industry="خدمات عامة",
            product_description=""
        )
        self.assertLessEqual(score, 50)
        self.assertEqual(breakdown["address"], 0)
        self.assertEqual(breakdown["business_name"], 10)

    def test_ai_fit_categories(self):
        self.assertEqual(calculate_ai_fit("عطور"), 25)
        self.assertEqual(calculate_ai_fit("شوكولاتة"), 25)
        self.assertEqual(calculate_ai_fit("ملابس نسائية"), 25)
        self.assertEqual(calculate_ai_fit("perfumes"), 25)
        self.assertEqual(calculate_ai_fit("أثاث وديكور"), 20)
        self.assertEqual(calculate_ai_fit("مطاعم وكافيهات"), 25)
        self.assertEqual(calculate_ai_fit("مدرسون خصوصيون"), 15)
        self.assertEqual(calculate_ai_fit("شركات برمجة"), 15)


if __name__ == "__main__":
    unittest.main()

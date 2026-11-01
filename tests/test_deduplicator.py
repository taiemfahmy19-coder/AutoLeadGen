import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from pipeline.deduplicator import Deduplicator, calculate_similarity


class MockDB:
    """Mock database for testing deduplicator."""

    def __init__(self):
        self.leads = []

    def get_all_leads(self):
        return self.leads

    def add_lead(self, lead_id, business_name, phone, address, website, industry, city):
        self.leads.append((
            lead_id, business_name, phone, address, website,
            industry, city, "search", 50, "NEW", "Arabic",
            "2026-01-01", "2026-01-01"
        ))


class TestDeduplicator(unittest.TestCase):

    def setUp(self):
        self.db = MockDB()
        self.dedup = Deduplicator(self.db)

    def test_calculate_similarity_exact(self):
        self.assertEqual(calculate_similarity("Ahmed Perfumes", "Ahmed Perfumes"), 100)
        self.assertEqual(calculate_similarity("عطور البرنس", "عطور البرنس"), 100)

    def test_calculate_similarity_partial(self):
        score = calculate_similarity("Ahmed Perfumes", "Ahmed Perfumes Cairo")
        self.assertGreater(score, 50)
        self.assertLess(score, 100)

    def test_calculate_similarity_none(self):
        self.assertEqual(calculate_similarity("Ahmed Perfumes", "Mohamed Electronics"), 0)

    def test_is_duplicate_level1_same_phone(self):
        # 01012345678 and +201012345678 normalize to same number
        self.db.add_lead(1, "Ahmed Perfumes", "01012345678", "Street 1", "site1.com", "Perfumes", "Cairo")

        is_dup, lead_id = self.dedup.is_duplicate(
            "Ahmed Store", "+201012345678", "Different Street", "site2.com"
        )
        self.assertTrue(is_dup)
        self.assertEqual(lead_id, 1)

    def test_is_duplicate_level2_same_website(self):
        self.db.add_lead(1, "Ahmed Perfumes", "01012345678", "Street 1", "https://ahmedperfumes.com", "Perfumes", "Cairo")

        is_dup, lead_id = self.dedup.is_duplicate(
            "Different Name", "01199999999", "Street 2", "http://www.ahmedperfumes.com"
        )
        self.assertTrue(is_dup)
        self.assertEqual(lead_id, 1)

    def test_is_duplicate_level3_same_name_address(self):
        self.db.add_lead(1, "Ahmed Perfumes", "01012345678", "123 Main Street Cairo", "site.com", "Perfumes", "Cairo")

        is_dup, lead_id = self.dedup.is_duplicate(
            "Ahmed Perfumes", "01111111111", "123 Main Street Cairo", "different.com"
        )
        self.assertTrue(is_dup)
        self.assertEqual(lead_id, 1)

    def test_is_duplicate_unique(self):
        self.db.add_lead(1, "Ahmed Perfumes", "01012345678", "Street 1", "site.com", "Perfumes", "Cairo")

        is_dup, lead_id = self.dedup.is_duplicate(
            "Mohamed Electronics", "01111111111", "Street 2", "site2.com"
        )
        self.assertFalse(is_dup)
        self.assertIsNone(lead_id)

    def test_get_duplicate_status(self):
        self.db.add_lead(1, "Ahmed Perfumes", "01012345678", "Street 1", "site.com", "Perfumes", "Cairo")

        status, reason = self.dedup.get_duplicate_status(
            "Ahmed Perfumes", "+201012345678", "Street 2", "site2.com"
        )
        self.assertEqual(status, "Duplicate (Same Phone Normalized)")
        self.assertEqual(reason, "phone_normalized")


if __name__ == "__main__":
    unittest.main()
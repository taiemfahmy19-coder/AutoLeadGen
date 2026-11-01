"""AutoLeadGen v2 - Comprehensive Unit Tests: Deduplication and Safe Merging."""
import sys
import os
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.repository import LeadRepository
from pipeline.deduplicator import Deduplicator, calculate_similarity


class TestDeduplicationEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_dedup.db")
        self.db = LeadRepository(self.db_path)
        self.dedup = Deduplicator(self.db)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exact_phone_duplicate(self):
        # Insert master lead
        lid1 = self.db.insert_lead("صيدلية النور", "+201012345678", "شارع التحرير", "", "أدوية", "القاهرة")
        # Check duplicate
        is_dup, match_id = self.dedup.is_duplicate("صيدلية النور فرع 2", "01012345678", "عنوان مختلف", "")
        self.assertTrue(is_dup)
        self.assertEqual(match_id, lid1)

    def test_exact_website_duplicate(self):
        lid1 = self.db.insert_lead("رويال للعطور", "+201011111111", "شارع شهاب", "https://royal-perfume.com", "عطور", "الجيزة")
        is_dup, match_id = self.dedup.is_duplicate("محل آخر", "+201022222222", "مكان آخر", "http://www.royal-perfume.com")
        self.assertTrue(is_dup)
        self.assertEqual(match_id, lid1)

    def test_name_and_address_similarity(self):
        lid1 = self.db.insert_lead("أحمد للعطور ومستحضرات التجميل", "+201011112222", "15 شارع عباس العقاد مدينة نصر", "", "عطور", "القاهرة")
        is_dup, match_id = self.dedup.is_duplicate("أحمد للعطور والتجميل", "", "15 شارع عباس العقاد مدينة نصر", "")
        self.assertTrue(is_dup)
        self.assertEqual(match_id, lid1)

    def test_critical_bug_fix_tail_phone_matching_prevented(self):
        """
        REGRESSION TEST FOR CRITICAL BUG:
        Two branches or distinct businesses with similar names MUST NOT be merged
        simply because they share the last 8 digits of a mobile subscriber number!
        Operator 010 (Vodafone) vs 011 (Etisalat).
        """
        # Branch 1 (Vodafone: 010)
        lid1 = self.db.insert_lead("صيدلية النور", "+201012345678", "فرع الدقي", "", "أدوية", "الجيزة")

        # Branch 2 (Etisalat: 011) - Same subscriber number (12345678)
        is_dup, match_id = self.dedup.is_duplicate("صيدلية النور", "+201112345678", "فرع المعادي", "")

        # MUST be considered Unique, NOT a duplicate!
        self.assertFalse(is_dup)
        self.assertIsNone(match_id)

    def test_merge_if_duplicate_atomic(self):
        lid1 = self.db.insert_lead("متجر الملابس", "+201033334444", "", "", "ملابس", "القاهرة")
        # Incoming lead with address and website
        merged_id, was_merged, reason = self.dedup.merge_if_duplicate(
            business_name="متجر الملابس",
            phone="01033334444",
            address="شارع فيصل",
            website="https://clothing-shop.com",
            industry="ملابس",
            city="الجيزة"
        )
        self.assertTrue(was_merged)
        self.assertEqual(merged_id, lid1)

        # Master record should now be updated
        master = self.db.get_lead_by_id(lid1)
        self.assertEqual(master[3], "شارع فيصل")
        self.assertEqual(master[4], "https://clothing-shop.com")


if __name__ == "__main__":
    unittest.main()

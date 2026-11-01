import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile
import shutil
from database import Database


class TestDatabase(unittest.TestCase):

    def setUp(self):
        # Create isolated temp database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_leads.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_tables(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "leads", "contacts", "interactions", "searches",
            "templates", "settings", "merge_history", "audit_log"
        ]
        for table in expected_tables:
            self.assertIn(table, tables)

    def test_insert_and_get_lead(self):
        lead_id = self.db.insert_lead(
            business_name="Ahmed Perfumes",
            phone="+201012345678",
            address="123 Main St",
            website="https://ahmedperfumes.com",
            industry="Perfumes",
            city="Cairo",
            source="search",
            score=95
        )

        self.assertIsInstance(lead_id, int)
        self.assertGreater(lead_id, 0)

        lead = self.db.get_lead_by_id(lead_id)
        self.assertIsNotNone(lead)
        self.assertEqual(lead[1], "Ahmed Perfumes")
        self.assertEqual(lead[2], "+201012345678")
        self.assertEqual(lead[5], "Perfumes")
        self.assertEqual(lead[6], "Cairo")
        self.assertEqual(lead[8], 95)
        self.assertEqual(lead[9], "NEW")

    def test_update_lead_status(self):
        lead_id = self.db.insert_lead("Test Store", "01012345678", "Addr", "site.com", "Industry", "City")
        self.db.update_lead_status(lead_id, "QUALIFIED")

        lead = self.db.get_lead_by_id(lead_id)
        self.assertEqual(lead[9], "QUALIFIED")

    def test_merge_leads(self):
        master_id = self.db.insert_lead("Master Store", "01011111111", "", "", "Perfumes", "Cairo")
        dup_id = self.db.insert_lead("Duplicate Store", "", "45 Tahrir St", "https://store.com", "Perfumes", "Cairo")

        success = self.db.merge_leads(master_id, dup_id, "Same owner")
        self.assertTrue(success)

        # Master now has merged address and website
        master = self.db.get_lead_by_id(master_id)
        self.assertEqual(master[3], "45 Tahrir St")
        self.assertEqual(master[4], "https://store.com")

        # Duplicate lead is deleted
        self.assertIsNone(self.db.get_lead_by_id(dup_id))

        # Merge history recorded
        history = self.db.get_merge_history()
        self.assertEqual(len(history), 1)

    def test_insert_interaction(self):
        lead_id = self.db.insert_lead("Test", "01012345678", "Addr", "site.com", "Industry", "City")
        self.db.insert_interaction(lead_id, channel="WhatsApp", message="Hello", status="SENT", notes="Outreach")

        interactions = self.db.get_interactions_for_lead(lead_id)
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0][3], "WhatsApp")
        self.assertEqual(interactions[0][4], "Hello")

    def test_get_dashboard_metrics(self):
        self.db.insert_lead("L1", "0101", "A", "W", "Ind", "C", score=40, status="NEW")
        self.db.insert_lead("L2", "0102", "A", "W", "Ind", "C", score=90, status="QUALIFIED")

        metrics = self.db.get_dashboard_metrics()
        self.assertEqual(metrics["total"], 2)
        self.assertEqual(metrics["new"], 1)
        self.assertEqual(metrics["qualified"], 1)
        self.assertEqual(metrics["avg_score"], 65.0)

    def test_auto_qualification_by_score(self):
        # Insert 3 leads with status NEW
        id1 = self.db.insert_lead("High Score Lead", "01011111111", "Addr", "site.com", "Perfumes", "Cairo", score=95, status="NEW")
        id2 = self.db.insert_lead("Mid Score Lead", "01022222222", "Addr", "site.com", "Perfumes", "Cairo", score=82, status="NEW")
        id3 = self.db.insert_lead("Low Score Lead", "01033333333", "Addr", "site.com", "Perfumes", "Cairo", score=60, status="NEW")

        # Run auto-qualification
        promoted = self.db.auto_qualify_new_leads(min_score=80)
        self.assertEqual(promoted, 2)

        # High & Mid become QUALIFIED
        self.assertEqual(self.db.get_lead_by_id(id1)[9], "QUALIFIED")
        self.assertEqual(self.db.get_lead_by_id(id2)[9], "QUALIFIED")
        # Low remains NEW
        self.assertEqual(self.db.get_lead_by_id(id3)[9], "NEW")

    def test_do_not_contact_never_auto_qualified(self):
        dnc_id = self.db.insert_lead("DNC Shop", "01012345678", "Addr", "site.com", "Perfumes", "Cairo", score=100, status="DO_NOT_CONTACT")
        
        # Run auto-qualify
        self.db.auto_qualify_new_leads(min_score=80)
        
        # Must stay DO_NOT_CONTACT
        self.assertEqual(self.db.get_lead_by_id(dnc_id)[9], "DO_NOT_CONTACT")

    def test_manual_status_never_overwritten_by_qualification(self):
        rep_id = self.db.insert_lead("Replied Shop", "01012345678", "Addr", "site.com", "Perfumes", "Cairo", score=95, status="REPLIED")
        int_id = self.db.insert_lead("Interested Shop", "01087654321", "Addr", "site.com", "Perfumes", "Cairo", score=90, status="INTERESTED")

        self.db.auto_qualify_new_leads(min_score=80)

        self.assertEqual(self.db.get_lead_by_id(rep_id)[9], "REPLIED")
        self.assertEqual(self.db.get_lead_by_id(int_id)[9], "INTERESTED")

    def test_promote_to_ready_criteria(self):
        # Lead 1: Complete data -> should be promoted
        ok_id = self.db.insert_lead("Complete Store", "01012345678", "Addr", "site.com", "Perfumes", "Cairo", score=90, status="QUALIFIED")
        # Lead 2: Missing phone -> should be rejected
        no_phone_id = self.db.insert_lead("No Phone Store", "", "Addr", "site.com", "Perfumes", "Cairo", score=90, status="QUALIFIED")
        # Lead 3: DNC -> should be rejected
        dnc_id = self.db.insert_lead("DNC Store", "01099999999", "Addr", "site.com", "Perfumes", "Cairo", score=95, status="DO_NOT_CONTACT")

        promoted, rejected = self.db.promote_to_ready([ok_id, no_phone_id, dnc_id])
        self.assertIn(ok_id, promoted)
        self.assertIn(no_phone_id, rejected)
        self.assertIn(dnc_id, rejected)

        self.assertEqual(self.db.get_lead_by_id(ok_id)[9], "READY")
        self.assertEqual(self.db.get_lead_by_id(dnc_id)[9], "DO_NOT_CONTACT")

    def test_whatsapp_status_field_and_update(self):
        lead_id = self.db.insert_lead(
            business_name="Test WA Biz",
            phone="+201011223344",
            address="Addr",
            website="",
            industry="عطور",
            city="القاهرة"
        )
        lead = self.db.get_lead_by_id(lead_id)
        # Check default status
        self.assertEqual(lead[13], "UNKNOWN")

        # Update to VERIFIED
        self.db.update_lead_whatsapp_status(lead_id, "VERIFIED")
        lead = self.db.get_lead_by_id(lead_id)
        self.assertEqual(lead[13], "VERIFIED")

        # Update to NOT_VERIFIED
        self.db.update_lead_whatsapp_status(lead_id, "NOT_VERIFIED")
        lead = self.db.get_lead_by_id(lead_id)
        self.assertEqual(lead[13], "NOT_VERIFIED")

    def test_promote_to_ready_rejects_not_verified(self):
        # Lead with valid phone and high score, but NOT_VERIFIED on WhatsApp
        lead_id = self.db.insert_lead(
            business_name="Unverified WA Biz",
            phone="+201055667788",
            address="Addr",
            website="",
            industry="عطور",
            city="القاهرة",
            score=90,
            status="QUALIFIED",
            whatsapp_status="NOT_VERIFIED"
        )
        promoted, rejected = self.db.promote_to_ready([lead_id])
        self.assertIn(lead_id, rejected)
        self.assertNotIn(lead_id, promoted)
        self.assertEqual(self.db.get_lead_by_id(lead_id)[9], "QUALIFIED")

    def test_dashboard_metrics_wa_statuses(self):
        self.db.insert_lead("WA1", "+201011111111", "a", "", "عطور", "القاهرة", whatsapp_status="VERIFIED")
        self.db.insert_lead("WA2", "+201022222222", "a", "", "عطور", "القاهرة", whatsapp_status="NOT_VERIFIED")
        self.db.insert_lead("WA3", "+201033333333", "a", "", "عطور", "القاهرة", whatsapp_status="UNKNOWN")
        metrics = self.db.get_dashboard_metrics()
        self.assertGreaterEqual(metrics["wa_verified"], 1)
        self.assertGreaterEqual(metrics["wa_not_verified"], 1)
        self.assertGreaterEqual(metrics["wa_unknown"], 1)

    def test_clear_all_leads(self):
        # Insert a lead
        lead_id = self.db.insert_lead("Test Clear", "+201099998888")
        self.assertGreater(len(self.db.get_all_leads()), 0)

        # Clear all leads
        deleted = self.db.clear_all_leads(reset_searches=True)
        self.assertGreaterEqual(deleted, 1)
        self.assertEqual(len(self.db.get_all_leads()), 0)
        self.assertEqual(len(self.db.get_searches()), 0)


if __name__ == "__main__":
    unittest.main()
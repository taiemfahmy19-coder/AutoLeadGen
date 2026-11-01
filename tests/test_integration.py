"""
Integration Test: Full AutoLeadGen Pipeline
Tests the complete flow:
  Search -> Clean -> Score -> Deduplicate -> SQLite -> CRM -> Message Queue
  -> DO_NOT_CONTACT enforcement -> Interaction Logging -> Export -> Backup
"""
import sys
import os
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.repository import LeadRepository as Database
from pipeline.cleaner import clean_data, normalize_phone
from pipeline.scorer import calculate_score
from pipeline.deduplicator import Deduplicator
from integrations.whatsapp_playwright import WhatsAppMessenger
from services.export_service import ExportService as Exporter
from database.backup_service import BackupService as BackupManager
from config.constants import (
    STATUS_NEW, STATUS_QUALIFIED, STATUS_READY,
    STATUS_CONTACTED, STATUS_DO_NOT_CONTACT, STATUS_INTERESTED
)


class TestFullPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "integration.db")
        self.profile_dir = os.path.join(self.temp_dir, "wa_profile")
        self.status_file = os.path.join(self.temp_dir, "wa_status.json")
        self.qr_path = os.path.join(self.temp_dir, "wa_qr.png")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.db = Database(self.db_path)
        self.dedup = Deduplicator(self.db)
        self.messenger = WhatsAppMessenger(
            db=self.db, profile_dir=self.profile_dir,
            status_file=self.status_file, qr_path=self.qr_path,
        )
        self.backup_mgr = BackupManager(db_path=self.db_path, backup_dir=self.backup_dir)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_cleaning_and_normalization(self):
        cleaned = clean_data(business_name="  عطورات  الملكي  ", phone="01012345678",
                             address="  12  street  ", website="http://www.test.com",
                             industry="عطور", city="القاهرة")
        self.assertEqual(cleaned["business_name"], "عطورات الملكي")
        self.assertEqual(cleaned["phone"], "+201012345678")
        self.assertEqual(cleaned["language"], "Arabic")

    def test_02_scoring_high_fit(self):
        score, _ = calculate_score(phone="+201012345678", website="https://example.com",
                                   business_name="عطورات الملكي", address="12 شارع", industry="عطور")
        self.assertGreaterEqual(score, 70)

    def test_03_insert_and_dedup_pipeline(self):
        lid1, was_merged, _ = self.dedup.merge_if_duplicate(
            "عطورات الملكي", "+201012345678", "addr1", "https://a.com", "عطور", "القاهرة", 90)
        self.assertFalse(was_merged)
        lid2, was_merged2, _ = self.dedup.merge_if_duplicate(
            "عطورات الملكي (fr)", "+201012345678", "addr2", "", "عطور", "القاهرة", 85)
        self.assertTrue(was_merged2)
        self.assertEqual(lid1, lid2)

    def test_04_crm_status_progression(self):
        lid = self.db.insert_lead("شوكولا رويال", "+201098765432", "addr",
                                  "https://rc.com", "شوكولاتة", "الجيزة", score=85)
        self.assertEqual(self.db.get_lead_by_id(lid)[9], STATUS_NEW)
        self.db.auto_qualify_new_leads(min_score=80)
        self.assertEqual(self.db.get_lead_by_id(lid)[9], STATUS_QUALIFIED)
        self.db.promote_to_ready([lid])
        self.assertEqual(self.db.get_lead_by_id(lid)[9], STATUS_READY)
        ok, _ = self.messenger.send_supervised(lid, "+201098765432", "Hi", delay=0)
        self.assertTrue(ok)
        self.assertEqual(self.db.get_lead_by_id(lid)[9], STATUS_CONTACTED)

    def test_05_do_not_contact_blocked(self):
        lid = self.db.insert_lead("Blocked", "+201011111111", "addr", "", "other", "Cairo", score=50)
        self.db.update_lead_status(lid, STATUS_DO_NOT_CONTACT)
        allowed, _ = self.messenger.can_contact(lead_id=lid)
        self.assertFalse(allowed)
        ok, _ = self.messenger.send_supervised(lid, "+201011111111", "spam")
        self.assertFalse(ok)
        interactions = self.db.get_interactions_for_lead(lid)
        self.assertEqual(len(interactions), 0)

    def test_06_interaction_logging(self):
        lid = self.db.insert_lead("Test Biz", "+201022222222", "a", "https://s.com", "ملابس", "Cairo", score=90)
        self.db.insert_interaction(lid, channel="WhatsApp", message="Hello", status="SENT", notes="test")
        ints = self.db.get_interactions_for_lead(lid)
        self.assertEqual(len(ints), 1)
        self.assertEqual(ints[0][3], "WhatsApp")

    def test_07_data_persists_after_restart(self):
        lid = self.db.insert_lead("Persistent", "+201033333333", "a", "", "عطور", "Cairo", score=90)
        self.db.close()
        db2 = Database(self.db_path)
        lead = db2.get_lead_by_id(lid)
        self.assertIsNotNone(lead)
        self.assertEqual(lead[1], "Persistent")
        db2.close()
        self.db = Database(self.db_path)

    def test_08_excel_export(self):
        self.db.insert_lead("Export", "+201044444444", "a", "", "عطور", "Cairo", score=90)
        leads = self.db.get_all_leads()
        path = os.path.join(self.temp_dir, "out.xlsx")
        result = Exporter.to_excel(leads, path)
        self.assertTrue(result)
        self.assertGreater(os.path.getsize(path), 0)

    def test_09_csv_export(self):
        self.db.insert_lead("CSV", "+201055555555", "a", "", "عطور", "Cairo", score=90)
        leads = self.db.get_all_leads()
        path = os.path.join(self.temp_dir, "out.csv")
        result = Exporter.to_csv(leads, path)
        self.assertTrue(result)
        with open(path, encoding="utf-8-sig") as f:
            self.assertIn("CSV", f.read())

    def test_10_backup_and_restore(self):
        lid = self.db.insert_lead("BkStore", "+201066666666", "a", "", "عطور", "Cairo", score=90)
        bk = self.backup_mgr.create_backup()
        self.assertTrue(os.path.exists(bk))
        self.db.delete_lead(lid)
        self.assertIsNone(self.db.get_lead_by_id(lid))
        self.backup_mgr.restore_backup(bk)
        self.db.close()
        self.db = Database(self.db_path)
        self.assertIsNotNone(self.db.get_lead_by_id(lid))

    def test_11_dashboard_metrics(self):
        id1 = self.db.insert_lead("A", "+201071111111", "a", "", "عطور", "Cairo", score=90)
        id2 = self.db.insert_lead("B", "+201072222222", "b", "", "عطور", "Cairo", score=90)
        self.db.update_lead_status(id1, STATUS_QUALIFIED)
        self.db.update_lead_status(id2, STATUS_DO_NOT_CONTACT)
        m = self.db.get_dashboard_metrics()
        self.assertGreaterEqual(m["qualified"], 1)
        self.assertGreaterEqual(m["do_not_contact"], 1)

    def test_12_whatsapp_initial_state(self):
        d = self.messenger.get_status_details()
        for key in ("status", "connected", "qr_available", "session_exists", "worker_running"):
            self.assertIn(key, d)
        self.assertEqual(d["status"], "DISCONNECTED")
        self.assertFalse(d["connected"])

    def test_13_no_interaction_logged_for_dnc(self):
        lid = self.db.insert_lead("DNC", "+201099999999", "a", "", "other", "Cairo", score=90)
        self.db.update_lead_status(lid, STATUS_DO_NOT_CONTACT)
        ok, _ = self.messenger.send_supervised(lid, "+201099999999", "spam", delay=0)
        self.assertFalse(ok)
        self.assertEqual(len(self.db.get_interactions_for_lead(lid)), 0)

    def test_14_whatsapp_status_integration_and_export(self):
        # Insert verified and unverified leads
        v_id = self.db.insert_lead("Verified Store", "+201088888888", "a", "", "عطور", "Cairo", score=95, whatsapp_status="VERIFIED")
        u_id = self.db.insert_lead("Unverified Store", "+201077777777", "b", "", "عطور", "Cairo", score=95, whatsapp_status="NOT_VERIFIED")

        leads = self.db.get_all_leads()
        m = self.db.get_dashboard_metrics()
        self.assertGreaterEqual(m["wa_verified"], 1)
        self.assertGreaterEqual(m["wa_not_verified"], 1)

        # Export to CSV and verify column exists
        csv_path = os.path.join(self.temp_dir, "test_wa_export.csv")
        Exporter.to_csv(leads, csv_path)
        with open(csv_path, encoding="utf-8-sig") as f:
            header = f.readline()
            self.assertIn("WhatsApp Status", header)

    def test_15_not_verified_lead_never_enters_ready_queue(self):
        # Lead has score 95, valid phone, but is NOT_VERIFIED on WhatsApp
        lid = self.db.insert_lead(
            "Fake WA Lead", "+201066666666", "a", "", "عطور", "Cairo",
            score=95, status="QUALIFIED", whatsapp_status="NOT_VERIFIED"
        )
        promoted, rejected = self.db.promote_to_ready([lid])
        self.assertIn(lid, rejected)
        self.assertNotIn(lid, promoted)

        # Sending message must also fail
        ok, reason = self.messenger.send_supervised(lid, "+201066666666", "msg", delay=0)
        self.assertFalse(ok)
        self.assertIn("WhatsApp", reason)


if __name__ == "__main__":
    unittest.main()


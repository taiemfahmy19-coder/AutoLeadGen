"""AutoLeadGen v2 - Comprehensive Integration Tests: End-to-End Pipeline."""
import sys
import os
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.repository import LeadRepository
from services.lead_service import LeadService
from services.outreach_service import OutreachService
from services.export_service import ExportService
from database.backup_service import BackupService
from config.constants import STATUS_NEW, STATUS_QUALIFIED, STATUS_READY, STATUS_CONTACTED


class TestEndToEndPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_e2e.db")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.db = LeadRepository(self.db_path)
        self.lead_svc = LeadService(self.db)
        self.outreach_svc = OutreachService(self.db)
        self.backup_svc = BackupService(db_path=self.db_path, backup_dir=self.backup_dir)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_pipeline_flow(self):
        # 1. Process and save lead with tricky Egyptian phone (+20 010...)
        res = self.lead_svc.process_and_save_lead(
            business_name="  عطورات  الملكي  ",
            phone="+20 010 1234 5678",
            address="شارع شهاب، المهندسين",
            website="http://www.royal-perfumes.com",
            industry="عطور",
            city="الجيزة",
            source="curated_seed"
        )
        lid = res["lead_id"]
        self.assertFalse(res["was_merged"])
        self.assertEqual(res["cleaned"]["phone"], "+201012345678")
        self.assertEqual(res["cleaned"]["business_name"], "عطورات الملكي")
        self.assertGreaterEqual(res["score"], 70)

        # 2. Verify lead status was auto-qualified because score >= 70
        lead = self.db.get_lead_by_id(lid)
        self.assertEqual(lead[9], STATUS_QUALIFIED)

        # 3. Duplicate incoming lead should be merged, not duplicated
        res_dup = self.lead_svc.process_and_save_lead(
            business_name="عطورات الملكي فرع الدقي",
            phone="01012345678",  # Same normalized number
            address="شارع شهاب، المهندسين",
            website="",
            industry="عطور",
            city="الجيزة"
        )
        self.assertTrue(res_dup["was_merged"])
        self.assertEqual(res_dup["lead_id"], lid)

        # 4. Promote to READY for outreach queue
        promoted, rejected = self.db.promote_to_ready([lid])
        self.assertIn(lid, promoted)
        self.assertEqual(self.db.get_lead_by_id(lid)[9], STATUS_READY)

        # 5. Fetch queue leads via OutreachService
        queue = self.outreach_svc.get_queue_leads()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0][0], lid)

        # 6. Export leads to CSV (UTF-8-BOM)
        csv_file = os.path.join(self.temp_dir, "test_e2e_leads.csv")
        out_csv = ExportService.to_csv(queue, csv_file)
        self.assertTrue(os.path.exists(out_csv))
        with open(out_csv, "r", encoding="utf-8-sig") as f:
            content = f.read()
            self.assertIn("عطورات الملكي", content)
            self.assertIn("+201012345678", content)

        # 7. Take consistent SQLite backup
        backup_file = self.backup_svc.create_backup("e2e_backup.db")
        self.assertTrue(os.path.exists(backup_file))


if __name__ == "__main__":
    unittest.main()

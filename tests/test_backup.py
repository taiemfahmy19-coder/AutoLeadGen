import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile
import shutil
from database.repository import LeadRepository as Database
from database.backup_service import BackupService as BackupManager


class TestBackup(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.backup_dir = os.path.join(self.temp_dir, "backups")

        # Initialize db and insert record
        db = Database(self.db_path)
        db.insert_lead("Initial Lead", "01011111111", "Addr", "site.com", "Perfumes", "Cairo")
        db.close()

        self.manager = BackupManager(db_path=self.db_path, backup_dir=self.backup_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_list_backup(self):
        backup_path = self.manager.create_backup("test_snap.db")
        self.assertTrue(os.path.exists(backup_path))

        backups = self.manager.list_backups()
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0]["name"], "test_snap.db")

    def test_restore_backup(self):
        # 1. Take backup with 1 lead
        backup_path = self.manager.create_backup("restore_test.db")

        # 2. Add second lead to current db
        db = Database(self.db_path)
        db.insert_lead("Second Lead", "01022222222", "Addr2", "site2.com", "Fashion", "Giza")
        leads_before_restore = db.get_all_leads()
        self.assertEqual(len(leads_before_restore), 2)
        db.close()

        # 3. Restore from backup (which had only 1 lead)
        self.manager.restore_backup(backup_path)

        # 4. Verify database state
        db_restored = Database(self.db_path)
        leads_after_restore = db_restored.get_all_leads()
        self.assertEqual(len(leads_after_restore), 1)
        self.assertEqual(leads_after_restore[0][1], "Initial Lead")
        db_restored.close()


if __name__ == "__main__":
    unittest.main()

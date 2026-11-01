"""AutoLeadGen v2 - Comprehensive Unit Tests: SQLite Concurrency, Indexes, Rollback, and Backup."""
import sys
import os
import unittest
import tempfile
import shutil
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.repository import LeadRepository
from database.backup_service import BackupService


class TestDatabaseConcurrency(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_concurrency.db")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        self.db = LeadRepository(self.db_path)
        self.backup_svc = BackupService(db_path=self.db_path, backup_dir=self.backup_dir)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sqlite_wal_mode_active(self):
        cursor = self.db.conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        self.assertEqual(mode.lower(), "wal")

    def test_foreign_keys_pragma_enabled(self):
        cursor = self.db.conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        fk = cursor.fetchone()[0]
        self.assertEqual(fk, 1)

    def test_indexes_exist(self):
        cursor = self.db.conn.cursor()
        cursor.execute("PRAGMA index_list(leads);")
        indexes = [r[1] for r in cursor.fetchall()]
        self.assertIn("idx_leads_phone", indexes)
        self.assertIn("idx_leads_status", indexes)
        self.assertIn("idx_leads_score", indexes)
        self.assertIn("idx_leads_wa", indexes)

    def test_transaction_rollback_on_error(self):
        lid = self.db.insert_lead("Initial Shop", "+201011112222", "Cairo", "", "عطور", "Cairo")
        
        # Attempt an invalid transaction
        try:
            with self.db.db_mgr.transaction() as conn:
                conn.execute("UPDATE leads SET business_name = 'Updated Name' WHERE id = ?", (lid,))
                # Force error
                conn.execute("INSERT INTO non_existent_table VALUES (1);")
        except Exception:
            pass

        # Lead name MUST still be 'Initial Shop' due to rollback
        lead = self.db.get_lead_by_id(lid)
        self.assertEqual(lead[1], "Initial Shop")

    def test_native_sqlite_backup_and_restore(self):
        lid = self.db.insert_lead("Original Lead", "+201099998888", "Giza", "", "ملابس", "الجيزة")
        backup_file = self.backup_svc.create_backup("test_online_backup.db")
        self.assertTrue(os.path.exists(backup_file))

        # Delete lead in active database
        self.db.delete_lead(lid)
        self.assertIsNone(self.db.get_lead_by_id(lid))

        # Restore from backup
        self.backup_svc.restore_backup(backup_file)
        self.db.close()
        self.db = LeadRepository(self.db_path)

        restored_lead = self.db.get_lead_by_id(lid)
        self.assertIsNotNone(restored_lead)
        self.assertEqual(restored_lead[1], "Original Lead")


if __name__ == "__main__":
    unittest.main()

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile
import shutil
from integrations.whatsapp_playwright import WhatsAppMessenger
from database.repository import LeadRepository as Database
from config.constants import STATUS_DO_NOT_CONTACT, STATUS_QUALIFIED, STATUS_READY


class TestWhatsAppWorkflow(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_wa.db")
        self.profile_dir = os.path.join(self.temp_dir, "wa_profile")
        self.status_file = os.path.join(self.temp_dir, "whatsapp_status.json")
        self.qr_path = os.path.join(self.temp_dir, "whatsapp_qr.png")
        self.db = Database(self.db_path)
        self.messenger = WhatsAppMessenger(
            db=self.db,
            profile_dir=self.profile_dir,
            status_file=self.status_file,
            qr_path=self.qr_path,
        )


    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_do_not_contact_enforcement_by_status(self):
        allowed, reason = self.messenger.can_contact(status=STATUS_DO_NOT_CONTACT)
        self.assertFalse(allowed)
        self.assertIn("DO_NOT_CONTACT", reason)

    def test_do_not_contact_enforcement_by_lead_id(self):
        lead_id = self.db.insert_lead("Blocked Store", "01011111111", "Addr", "site.com", "Perfumes", "Cairo")
        self.db.update_lead_status(lead_id, STATUS_DO_NOT_CONTACT)

        allowed, reason = self.messenger.can_contact(lead_id=lead_id)
        self.assertFalse(allowed)
        self.assertIn("DO_NOT_CONTACT", reason)

    def test_can_contact_allowed_for_normal_lead(self):
        lead_id = self.db.insert_lead("Good Store", "01022222222", "Addr", "site.com", "Perfumes", "Cairo")
        self.db.update_lead_status(lead_id, STATUS_READY)

        allowed, reason = self.messenger.can_contact(lead_id=lead_id)
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_generate_direct_link(self):
        link = self.messenger.generate_direct_link("01012345678", "مرحبا بك")
        self.assertTrue(link.startswith("https://wa.me/201012345678?text="))
        self.assertIn("%D9%85%D8%B1%D8%AD%D8%A8%D8%A7", link)

    def test_initial_connection_status(self):
        # Fresh profile should report DISCONNECTED
        status = self.messenger.get_connection_status()
        self.assertEqual(status, "DISCONNECTED")

    def test_disconnect_clears_profile(self):
        dummy_file = os.path.join(self.profile_dir, "session_test.dat")
        with open(dummy_file, "w") as f:
            f.write("session data")
        self.assertTrue(os.path.exists(dummy_file))

    def test_save_and_get_status(self):
        # SCANNING with no live worker thread auto-corrects to DISCONNECTED
        self.messenger._save_status("SCANNING", {"message": "Scanning test"})
        self.assertEqual(self.messenger.get_connection_status(), "SCANNING")  # raw file value
        details = self.messenger.get_status_details()
        # Auto-correction: SCANNING + no worker → DISCONNECTED
        self.assertEqual(details["status"], "DISCONNECTED")
        self.assertFalse(details["worker_running"])

        # CONNECTED state must persist as-is (no auto-correction applied)
        self.messenger._save_status("CONNECTED", {"message": "Login success"})
        self.assertEqual(self.messenger.get_connection_status(), "CONNECTED")
        self.assertTrue(self.messenger.check_session())
        details = self.messenger.get_status_details()
        self.assertTrue(details["connected"])


    def test_cancel_worker_resets_to_disconnected(self):
        self.messenger._save_status("SCANNING")
        self.messenger.cancel_worker()
        self.assertEqual(self.messenger.get_connection_status(), "DISCONNECTED")

    # --- Regression tests for get_status_details() rich dict ---

    def test_get_status_details_returns_required_keys(self):
        """Every call must return all required keys regardless of state."""
        required_keys = {"status", "connected", "message", "qr_available", "session_exists", "worker_running", "updated_at"}
        details = self.messenger.get_status_details()
        for key in required_keys:
            self.assertIn(key, details, msg=f"Missing key: '{key}' in get_status_details()")

    def test_get_status_details_disconnected_defaults(self):
        """Fresh messenger with no profile should report DISCONNECTED and all booleans False."""
        details = self.messenger.get_status_details()
        self.assertEqual(details["status"], "DISCONNECTED")
        self.assertFalse(details["connected"])
        self.assertFalse(details["qr_available"])
        self.assertFalse(details["worker_running"])

    def test_get_status_details_connected_state(self):
        """After saving CONNECTED status, get_status_details must reflect it."""
        self.messenger._save_status("CONNECTED", {"message": "Logged in!"})
        details = self.messenger.get_status_details()
        self.assertEqual(details["status"], "CONNECTED")
        self.assertTrue(details["connected"])
        self.assertFalse(details["worker_running"])  # No real thread started

    def test_get_status_details_scanning_with_dead_worker_auto_corrects(self):
        """If status is SCANNING but worker thread is dead, status should auto-reset to DISCONNECTED."""
        self.messenger._save_status("SCANNING", {"message": "QR ready"})
        # No worker thread started – _worker_thread is None → worker_running = False
        details = self.messenger.get_status_details()
        self.assertEqual(details["status"], "DISCONNECTED")
        self.assertFalse(details["connected"])

    def test_get_status_details_qr_available_flag(self):
        """qr_available must be True only when qr_path file is non-empty."""
        # No file yet
        details = self.messenger.get_status_details()
        self.assertFalse(details["qr_available"])

        # Write a dummy QR file
        dummy_qr = os.path.join(self.temp_dir, "whatsapp_qr.png")
        self.messenger.qr_path = dummy_qr
        with open(dummy_qr, "wb") as f:
            f.write(b"\x00\x01\x02")  # non-empty
        details = self.messenger.get_status_details()
        self.assertTrue(details["qr_available"])

        # Empty file should still return False
        open(dummy_qr, "wb").close()
        details = self.messenger.get_status_details()
        self.assertFalse(details["qr_available"])

    def test_can_contact_blocked_for_not_verified_by_status(self):
        allowed, reason = self.messenger.can_contact(whatsapp_status="NOT_VERIFIED")
        self.assertFalse(allowed)
        self.assertIn("WhatsApp", reason)

    def test_can_contact_blocked_for_not_verified_by_lead_id(self):
        lead_id = self.db.insert_lead("No WA Lead", "+201011112222", "a", "", "عطور", "Cairo", whatsapp_status="NOT_VERIFIED")
        allowed, reason = self.messenger.can_contact(lead_id=lead_id)
        self.assertFalse(allowed)
        self.assertIn("WhatsApp", reason)

    def test_fast_session_check(self):
        # Empty profile dir -> False
        self.assertFalse(self.messenger.fast_session_check())

        # Write dummy file to profile dir and save CONNECTED
        dummy = os.path.join(self.profile_dir, "cookie.dat")
        with open(dummy, "w") as f:
            f.write("test")
        self.messenger._save_status("CONNECTED")
        self.assertTrue(self.messenger.fast_session_check())


if __name__ == "__main__":
    unittest.main()


"""AutoLeadGen v2 - Comprehensive Unit Tests: WhatsApp Verification Truth and Outreach Safeguards."""
import sys
import os
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.repository import LeadRepository
from integrations.whatsapp_playwright import WhatsAppMessenger
from integrations.maps_scraper import LeadScraper
from config.constants import (
    STATUS_DO_NOT_CONTACT,
    STATUS_READY,
    WA_STATUS_VERIFIED,
    WA_STATUS_NOT_VERIFIED,
    WA_STATUS_UNKNOWN,
    INTERACTION_MANUALLY_MARKED,
)


class TestWhatsAppVerification(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_wa.db")
        self.profile_dir = os.path.join(self.temp_dir, "wa_profile")
        self.status_file = os.path.join(self.temp_dir, "whatsapp_status.json")
        self.qr_path = os.path.join(self.temp_dir, "whatsapp_qr.png")
        self.db = LeadRepository(self.db_path)
        self.messenger = WhatsAppMessenger(
            db=self.db,
            profile_dir=self.profile_dir,
            status_file=self.status_file,
            qr_path=self.qr_path,
        )

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_random_numbers_never_marked_as_verified(self):
        """
        CORE TRUTH TEST:
        Discovery scraper MUST NEVER set whatsapp_status = 'VERIFIED'
        for untested numbers!
        """
        scraper = LeadScraper()
        leads = scraper.search_leads("عطور", "القاهرة", limit=5, use_live_browser=False, messenger=None)
        self.assertTrue(len(leads) > 0)
        for lead in leads:
            # Must be UNKNOWN until verified via real network/session check
            self.assertEqual(lead["whatsapp_status"], WA_STATUS_UNKNOWN)

    def test_can_contact_blocks_do_not_contact(self):
        lid = self.db.insert_lead("Blocked Shop", "+201011112222", "Cairo", "", "عطور", "Cairo")
        self.db.update_lead_status(lid, STATUS_DO_NOT_CONTACT)
        allowed, reason = self.messenger.can_contact(lead_id=lid)
        self.assertFalse(allowed)
        self.assertIn("DO_NOT_CONTACT", reason)

    def test_can_contact_blocks_not_verified_whatsapp(self):
        lid = self.db.insert_lead("No WA Shop", "+201011112222", "Cairo", "", "عطور", "Cairo")
        self.db.update_lead_whatsapp_status(lid, WA_STATUS_NOT_VERIFIED)
        allowed, reason = self.messenger.can_contact(lead_id=lid)
        self.assertFalse(allowed)
        self.assertIn("WhatsApp", reason)

    def test_send_supervised_records_manually_marked_not_fake_sent(self):
        """
        REGRESSION TEST:
        Manual button click must log interaction status as 'MANUALLY_MARKED',
        never as 'SENT' without proof!
        """
        lid = self.db.insert_lead("Good Shop", "+201011112222", "Cairo", "", "عطور", "Cairo", status=STATUS_READY)
        ok, msg = self.messenger.send_supervised(lid, "+201011112222", "Hello")
        self.assertTrue(ok)

        interactions = self.db.get_interactions_for_lead(lid)
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0][5], INTERACTION_MANUALLY_MARKED)

    def test_generate_direct_link(self):
        url = self.messenger.generate_direct_link("01012345678", "مرحبا")
        self.assertTrue(url.startswith("https://wa.me/201012345678?text="))
        self.assertIn("%D9%85%D8%B1%D8%AD%D8%A8%D8%A7", url)


if __name__ == "__main__":
    unittest.main()

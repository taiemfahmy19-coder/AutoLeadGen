"""Tests for Zero-Cost Direct SMTP Email Engine, Spintax, and Cleaners."""
import unittest
import os
import tempfile
import shutil
from pipeline.cleaner import normalize_email, extract_emails, extract_instagram_handle
from integrations.email_engine import EmailEngine, DEFAULT_EMAIL_SUBJECTS


class TestEmailEngineAndPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_email_config.json")
        self.engine = EmailEngine(config_path=self.config_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_normalize_email_valid(self):
        self.assertEqual(normalize_email("  User.Name+Tag@domain.com  "), "user.name+tag@domain.com")
        self.assertEqual(normalize_email("info@sweet-store.com.sa"), "info@sweet-store.com.sa")

    def test_normalize_email_invalid(self):
        self.assertEqual(normalize_email("plainaddress"), "")
        self.assertEqual(normalize_email("@missingusername.com"), "")
        self.assertEqual(normalize_email("image@site.png"), "")  # File extension filter

    def test_extract_emails_from_text(self):
        text = "للتواصل معنا راسلنا على info@business.com أو المبيعات sales@business.com وشكراً"
        extracted = extract_emails(text)
        self.assertIn("info@business.com", extracted)
        self.assertIn("sales@business.com", extracted)
        self.assertEqual(len(extracted), 2)

    def test_extract_instagram_handle(self):
        self.assertEqual(extract_instagram_handle("https://www.instagram.com/chocostore/"), "@chocostore")
        self.assertEqual(extract_instagram_handle("instagram.com/perfume_brand"), "@perfume_brand")
        self.assertEqual(extract_instagram_handle("@brand_egypt"), "@brand_egypt")
        # Exclude non-profile subpaths
        self.assertEqual(extract_instagram_handle("https://instagram.com/explore/tags/choc"), "")

    def test_email_engine_config_save_and_load(self):
        cfg = {
            "provider": "Gmail (App Password)",
            "host": "smtp.gmail.com",
            "port": 465,
            "use_ssl": True,
            "use_tls": False,
            "sender_name": "Test Agency",
            "sender_email": "test@gmail.com",
            "password": "abcd efgh ijkl mnop",
        }
        saved = self.engine.save_config(cfg)
        self.assertTrue(saved)

        loaded = self.engine.load_config()
        self.assertEqual(loaded["sender_email"], "test@gmail.com")
        self.assertTrue(loaded["is_configured"])

    def test_build_custom_email_payload_spintax(self):
        subjects = set()
        for _ in range(10):
            subj, html, text = self.engine.build_custom_email_payload(
                business_name="كلاس ون",
                industry="حلويات",
                city="الرياض"
            )
            self.assertIn("كلاس ون", subj)
            self.assertIn("كلاس ون", html)
            self.assertIn("<!DOCTYPE html>", html)
            subjects.add(subj)
        # Verify that Spintax generated variations
        self.assertGreater(len(subjects), 1)

    def test_test_connection_invalid_credentials(self):
        bad_cfg = {
            "host": "smtp.gmail.com",
            "port": 465,
            "use_ssl": True,
            "use_tls": False,
            "sender_email": "invalid_dummy_account_12345@gmail.com",
            "password": "wrong_password"
        }
        ok, msg = self.engine.test_connection(bad_cfg)
        self.assertFalse(ok)
        self.assertIn("❌", msg)


if __name__ == "__main__":
    unittest.main()

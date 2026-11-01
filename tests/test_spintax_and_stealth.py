"""Tests for Spintax variations, stealth helpers, and anti-ban safety limits."""
import unittest
from services.outreach_service import OutreachService
from config.constants import (
    WHATSAPP_DELAY_MIN,
    WHATSAPP_DELAY_MAX,
    WHATSAPP_BATCH_SIZE,
    WHATSAPP_COOLDOWN_MIN,
    WHATSAPP_COOLDOWN_MAX,
    WHATSAPP_DAILY_RECOMMENDED_MAX
)
from integrations.whatsapp_playwright import _bezier_point


class TestSpintaxAndAntiBan(unittest.TestCase):

    def test_spintax_basic_options(self):
        pattern = "{مرحبا|أهلا|سلام}"
        results = set()
        for _ in range(30):
            res = OutreachService.parse_spintax(pattern)
            self.assertIn(res, ["مرحبا", "أهلا", "سلام"])
            results.add(res)
        self.assertGreater(len(results), 1)

    def test_spintax_leaves_non_pipe_braces_intact(self):
        pattern = "مرحبا {business} في {city}"
        res = OutreachService.parse_spintax(pattern)
        self.assertEqual(res, "مرحبا {business} في {city}")

    def test_spintax_nested(self):
        pattern = "{صباح الخير|{مساء|نهارك} سعيد}"
        possible = ["صباح الخير", "مساء سعيد", "نهارك سعيد"]
        results = set()
        for _ in range(40):
            res = OutreachService.parse_spintax(pattern)
            self.assertIn(res, possible)
            results.add(res)
        self.assertGreater(len(results), 1)

    def test_build_personalized_message_generates_varied_hashes(self):
        messages = set()
        for _ in range(15):
            msg = OutreachService.build_personalized_message("برفانات الرياض", "عطور", "الرياض")
            self.assertIn("برفانات الرياض", msg)
            self.assertIn("عطور", msg)
            self.assertIn("الرياض", msg)
            messages.add(msg)
        self.assertGreaterEqual(len(messages), 4)

    def test_safety_bounds_constants(self):
        self.assertGreaterEqual(WHATSAPP_DELAY_MIN, 60, "Delay min should be at least 60s for cold chats")
        self.assertGreaterEqual(WHATSAPP_DELAY_MAX, 120, "Delay max should be at least 120s for cold chats")
        self.assertLessEqual(WHATSAPP_BATCH_SIZE, 10, "Batch size burst must be 10 or fewer leads")
        self.assertGreaterEqual(WHATSAPP_COOLDOWN_MIN, 600, "Cooldown min should be at least 10 minutes")
        self.assertLessEqual(WHATSAPP_DAILY_RECOMMENDED_MAX, 50, "Safe daily max should not exceed 50")

    def test_bezier_curve_endpoints(self):
        p0, p1, p2, p3 = 10.0, 30.0, 70.0, 100.0
        start = _bezier_point(p0, p1, p2, p3, 0.0)
        end = _bezier_point(p0, p1, p2, p3, 1.0)
        mid = _bezier_point(p0, p1, p2, p3, 0.5)

        self.assertAlmostEqual(start, 10.0)
        self.assertAlmostEqual(end, 100.0)
        self.assertTrue(10.0 < mid < 100.0)


if __name__ == "__main__":
    unittest.main()

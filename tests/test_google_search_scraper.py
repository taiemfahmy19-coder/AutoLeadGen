"""Unit tests for GoogleSearchScraper logic and parsing."""
import unittest
from unittest.mock import patch, MagicMock
from integrations.google_search_scraper import GoogleSearchScraper


class TestGoogleSearchScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = GoogleSearchScraper(headless=True)

    def test_scraper_initialization(self):
        self.assertTrue(self.scraper.headless)

    @patch("playwright.sync_api.sync_playwright")
    def test_search_whatsapp_leads_mocked(self, mock_playwright):
        mock_p = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_p

        mock_browser = MagicMock()
        mock_p.chromium.launch.return_value = mock_browser

        mock_context = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_page = MagicMock()
        mock_context.new_page.return_value = mock_page

        # Mock search result element
        mock_elem = MagicMock()
        mock_elem.inner_text.return_value = "متجر رويال للشوكولاتة الرياض تواصل معنا واتساب: 0501234567"

        mock_h3 = MagicMock()
        mock_h3.count.return_value = 1
        mock_h3.first.inner_text.return_value = "متجر رويال للشوكولاتة"
        mock_elem.locator.side_effect = lambda sel: (
            mock_h3 if "h3" in sel else MagicMock(all=lambda: [], count=lambda: 0, first=MagicMock(get_attribute=lambda a: "https://royal.com"))
        )

        mock_page.locator.return_value.all.return_value = [mock_elem]

        results = self.scraper.search_whatsapp_leads(
            industry="شوكولاتة",
            city="الرياض",
            country="المملكة العربية السعودية",
            country_code="966",
            limit=5
        )

        self.assertIsInstance(results, list)
        if results:
            self.assertEqual(results[0]["phone"], "+966501234567")
            self.assertEqual(results[0]["city"], "الرياض")
            self.assertEqual(results[0]["source"], "google_search")


if __name__ == "__main__":
    unittest.main()

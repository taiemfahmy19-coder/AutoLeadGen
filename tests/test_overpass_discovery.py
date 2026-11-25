"""AutoLeadGen V3 — Tests for Overpass Discovery Engine (no real HTTP calls)."""
import unittest
from unittest.mock import patch, MagicMock

from integrations.overpass_discovery import (
    _build_overpass_query,
    _extract_lead_from_element,
    search_city,
)


class TestQueryBuilder(unittest.TestCase):
    def test_query_contains_city(self):
        q = _build_overpass_query("Cairo", "Egypt", "all", limit=50)
        self.assertIn("Cairo", q)

    def test_query_contains_timeout(self):
        q = _build_overpass_query("Cairo", "Egypt", "all")
        self.assertIn("[timeout:", q)

    def test_query_specific_type(self):
        q = _build_overpass_query("Dubai", "UAE", "restaurant", limit=100)
        self.assertIn("area", q)
        self.assertIn("[out:json]", q)


class TestNormalizeNode(unittest.TestCase):
    def _node(self, **tags):
        return {"type": "node", "lat": 30.05, "lon": 31.23, "tags": tags}

    def test_name_extracted(self):
        el = self._node(name="Cairo Restaurant", amenity="restaurant")
        lead = _extract_lead_from_element(el, "Cairo", "Egypt", "http://example.com")
        self.assertIsNotNone(lead)
        self.assertEqual(lead["business_name"], "Cairo Restaurant")

    def test_coordinates_extracted(self):
        el = self._node(name="Test Shop", shop="grocery")
        lead = _extract_lead_from_element(el, "Cairo", "Egypt", "http://x.com")
        self.assertEqual(lead["latitude"], 30.05)
        self.assertEqual(lead["longitude"], 31.23)
        self.assertEqual(lead["coord_source"], "overpass")
        self.assertEqual(lead["coord_verified"], 1)

    def test_phone_email_website_extracted(self):
        el = self._node(
            name="Clinic X",
            amenity="clinic",
            phone="+201012345678",
            email="clinic@example.com",
            website="https://clinicx.com",
        )
        lead = _extract_lead_from_element(el, "Cairo", "Egypt", "http://x.com")
        self.assertEqual(lead["phone"], "+201012345678")
        self.assertEqual(lead["email"], "clinic@example.com")
        self.assertEqual(lead["website"], "https://clinicx.com")

    def test_country_set(self):
        el = self._node(name="Hotel Dubai", tourism="hotel")
        lead = _extract_lead_from_element(el, "Dubai", "UAE", "http://x.com")
        self.assertEqual(lead["country"], "UAE")
        self.assertEqual(lead["city"], "Dubai")

    def test_data_confidence_set(self):
        el = self._node(name="Office B", office="it")
        lead = _extract_lead_from_element(el, "Riyadh", "Saudi Arabia", "http://x.com")
        self.assertEqual(lead["data_confidence"], "medium")
        self.assertEqual(lead["source"], "overpass")


class TestNormalizeWayWithCenter(unittest.TestCase):
    def test_way_uses_center(self):
        el = {
            "type": "way",
            "center": {"lat": 25.1, "lon": 55.2},
            "tags": {"name": "Mall of Emirates", "shop": "mall"},
        }
        lead = _extract_lead_from_element(el, "Dubai", "UAE", "http://x.com")
        self.assertIsNotNone(lead)
        self.assertAlmostEqual(lead["latitude"], 25.1)
        self.assertAlmostEqual(lead["longitude"], 55.2)

    def test_way_without_center_has_null_coords(self):
        el = {
            "type": "way",
            "tags": {"name": "No Center Shop", "shop": "grocery"},
        }
        lead = _extract_lead_from_element(el, "Cairo", "Egypt", "http://x.com")
        self.assertIsNotNone(lead)
        self.assertIsNone(lead["latitude"])
        self.assertIsNone(lead["longitude"])
        self.assertEqual(lead["coord_source"], "")
        self.assertEqual(lead["coord_verified"], 0)


class TestSkipUnnamed(unittest.TestCase):
    def test_missing_name_returns_none(self):
        el = {"type": "node", "lat": 30.0, "lon": 31.0, "tags": {"amenity": "restaurant"}}
        lead = _extract_lead_from_element(el, "Cairo", "Egypt", "http://x.com")
        self.assertIsNone(lead)

    def test_empty_name_returns_none(self):
        el = {"type": "node", "lat": 30.0, "lon": 31.0, "tags": {"name": "   ", "shop": "grocery"}}
        lead = _extract_lead_from_element(el, "Cairo", "Egypt", "http://x.com")
        self.assertIsNone(lead)


class TestSearchCityMocked(unittest.TestCase):
    @patch("integrations.overpass_discovery.requests.post")
    def test_yields_leads_from_response(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "elements": [
                {"type": "node", "lat": 30.0, "lon": 31.0, "tags": {"name": "Café Nile", "amenity": "cafe"}},
                {"type": "node", "lat": 30.1, "lon": 31.1, "tags": {"name": "", "amenity": "bar"}},  # no name → skip
                {"type": "node", "lat": 29.9, "lon": 30.9, "tags": {"name": "Spice Market", "shop": "spices"}},
            ]
        }
        mock_post.return_value = mock_resp
        with patch("integrations.overpass_discovery.time.sleep"):
            results = list(search_city("Cairo", "Egypt", business_type="all"))
        self.assertEqual(len(results), 2)
        names = {r["business_name"] for r in results}
        self.assertIn("Café Nile", names)
        self.assertIn("Spice Market", names)

    @patch("integrations.overpass_discovery.requests.post")
    def test_rate_limit_retries(self, mock_post):
        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        mock_resp_ok.json.return_value = {
            "elements": [
                {"type": "node", "lat": 25.0, "lon": 55.0, "tags": {"name": "Shop A", "shop": "grocery"}}
            ]
        }
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_post.side_effect = [mock_resp_429, mock_resp_ok]

        with patch("integrations.overpass_discovery.time.sleep"):
            results = list(search_city("Dubai", "UAE"))
        self.assertEqual(len(results), 1)

    @patch("integrations.overpass_discovery.requests.post")
    def test_cancel_stops_iteration(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "elements": [
                {"type": "node", "lat": 30.0, "lon": 31.0, "tags": {"name": f"Shop {i}", "shop": "grocery"}}
                for i in range(100)
            ]
        }
        mock_post.return_value = mock_resp
        cancelled = {"flag": True}
        with patch("integrations.overpass_discovery.time.sleep"):
            results = list(search_city("Cairo", "Egypt", cancel_check=lambda: cancelled["flag"]))
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()

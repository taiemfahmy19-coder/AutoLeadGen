import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from pipeline.cleaner import clean_data, normalize_phone, clean_business_name, clean_address, clean_website, detect_language


class TestCleaner(unittest.TestCase):

    def test_normalize_phone_egyptian_mobile(self):
        # Egyptian mobile numbers
        self.assertEqual(normalize_phone("01012345678"), "+201012345678")
        self.assertEqual(normalize_phone("01112345678"), "+201112345678")
        self.assertEqual(normalize_phone("01212345678"), "+201212345678")
        self.assertEqual(normalize_phone("01512345678"), "+201512345678")

    def test_normalize_phone_with_country_code(self):
        self.assertEqual(normalize_phone("+201012345678"), "+201012345678")
        self.assertEqual(normalize_phone("00201012345678"), "+201012345678")
        self.assertEqual(normalize_phone("201012345678"), "+201012345678")

    def test_normalize_phone_with_arabic_indic_numerals(self):
        # ٠١٠١٢٣٤٥٦٧٨ -> +201012345678
        self.assertEqual(normalize_phone("٠١٠١٢٣٤٥٦٧٨"), "+201012345678")

    def test_normalize_phone_with_spaces_and_dashes(self):
        self.assertEqual(normalize_phone("010-1234-5678"), "+201012345678")
        self.assertEqual(normalize_phone("+20 (10) 1234 5678"), "+201012345678")

    def test_normalize_phone_invalid_or_empty(self):
        self.assertEqual(normalize_phone(""), "")
        self.assertEqual(normalize_phone(None), "")

    def test_clean_business_name(self):
        self.assertEqual(clean_business_name("  Ahmed  Perfumes  "), "Ahmed Perfumes")
        self.assertEqual(clean_business_name("عطورات   البرنس \n القاهرة"), "عطورات البرنس القاهرة")
        self.assertEqual(clean_business_name(""), "")
        self.assertEqual(clean_business_name("   "), "")

    def test_clean_address(self):
        self.assertEqual(clean_address("  Street 1  ,  City  "), "Street 1, City")
        self.assertEqual(clean_address(""), "")

    def test_clean_website(self):
        self.assertEqual(clean_website("example.com"), "https://example.com")
        self.assertEqual(clean_website("https://example.com/"), "https://example.com")
        self.assertEqual(clean_website("http://example.com"), "https://example.com")
        self.assertEqual(clean_website("www.example.com"), "https://example.com")
        self.assertEqual(clean_website(""), "")

    def test_detect_language(self):
        self.assertEqual(detect_language("محل عطور", city="القاهرة"), "Arabic")
        self.assertEqual(detect_language("John Doe Tech", city="London"), "English")

    def test_clean_data(self):
        result = clean_data(
            business_name="  Ahmed Perfumes  ",
            phone="01012345678",
            address="  Street 1, Cairo  ",
            website="perfumes.com",
            industry="Perfumes",
            city="Cairo"
        )

        self.assertEqual(result["business_name"], "Ahmed Perfumes")
        self.assertEqual(result["phone"], "+201012345678")
        self.assertEqual(result["address"], "Street 1, Cairo")
        self.assertEqual(result["website"], "https://perfumes.com")
        self.assertEqual(result["industry"], "Perfumes")
        self.assertEqual(result["city"], "Cairo")


if __name__ == "__main__":
    unittest.main()
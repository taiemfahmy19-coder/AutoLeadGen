"""AutoLeadGen v2 - Comprehensive Unit Tests: Phone Normalization & Whitelist Validation."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.cleaner import normalize_phone, is_mobile_phone, get_phone_validity
from config.constants import PHONE_VALID, PHONE_LANDLINE, PHONE_INVALID, PHONE_UNKNOWN


class TestPhoneNormalization(unittest.TestCase):

    def test_standard_egyptian_mobiles(self):
        self.assertEqual(normalize_phone("01012345678"), "+201012345678")
        self.assertEqual(normalize_phone("01112345678"), "+201112345678")
        self.assertEqual(normalize_phone("01212345678"), "+201212345678")
        self.assertEqual(normalize_phone("01512345678"), "+201512345678")

    def test_egyptian_mobile_with_country_code_and_zero(self):
        # Critical Bug Fix: +20 010... -> +2010... (not +20010...)
        self.assertEqual(normalize_phone("+20 010 1234 5678"), "+201012345678")
        self.assertEqual(normalize_phone("0020 011 1234 5678"), "+201112345678")
        self.assertEqual(normalize_phone("2001212345678"), "+201212345678")
        self.assertEqual(normalize_phone("+2001512345678"), "+201512345678")

    def test_egyptian_mobile_with_erroneous_plus(self):
        # Critical Bug Fix: +010... -> +2010...
        self.assertEqual(normalize_phone("+01012345678"), "+201012345678")

    def test_arabic_indic_numerals(self):
        self.assertEqual(normalize_phone("٠١٠١٢٣٤٥٦٧٨"), "+201012345678")
        self.assertEqual(normalize_phone("+٢٠١٠١٢٣٤٥٦٧٨"), "+201012345678")

    def test_saudi_mobiles(self):
        self.assertEqual(normalize_phone("0541234567"), "+966541234567")
        self.assertEqual(normalize_phone("0501234567", default_country_code="966"), "+966501234567")
        self.assertEqual(normalize_phone("+966 50 123 4567"), "+966501234567")
        self.assertEqual(normalize_phone("00966501234567"), "+966501234567")

    def test_uae_mobiles(self):
        self.assertEqual(normalize_phone("0501234567", default_country_code="971"), "+971501234567")
        self.assertEqual(normalize_phone("+971 50 123 4567"), "+971501234567")

    def test_egyptian_landlines_normalized(self):
        self.assertEqual(normalize_phone("0233445566"), "+20233445566")      # Cairo
        self.assertEqual(normalize_phone("035544332"), "+2035544332")        # Alexandria
        self.assertEqual(normalize_phone("0133221234"), "+20133221234")      # Benha / Qalyubia
        self.assertEqual(normalize_phone("0403331234"), "+20403331234")      # Tanta
        self.assertEqual(normalize_phone("0502221234"), "+20502221234")      # Mansoura
        self.assertEqual(normalize_phone("0623331234"), "+20623331234")      # Suez
        self.assertEqual(normalize_phone("0643331234"), "+20643331234")      # Ismailia

    def test_is_mobile_phone_strictly_whitelisted(self):
        # Egyptian Mobiles: True
        self.assertTrue(is_mobile_phone("+201012345678"))
        self.assertTrue(is_mobile_phone("+201112345678"))
        self.assertTrue(is_mobile_phone("+201212345678"))
        self.assertTrue(is_mobile_phone("+201512345678"))

        # Saudi & UAE Mobiles: True
        self.assertTrue(is_mobile_phone("+966501234567"))
        self.assertTrue(is_mobile_phone("+971501234567"))

        # All Egyptian Landlines MUST BE REJECTED: False
        self.assertFalse(is_mobile_phone("+20233445566"))   # Cairo (02)
        self.assertFalse(is_mobile_phone("+2035544332"))    # Alex (03)
        self.assertFalse(is_mobile_phone("+20133221234"))   # Benha (013) - Critical Fix!
        self.assertFalse(is_mobile_phone("+20403331234"))   # Tanta (040)
        self.assertFalse(is_mobile_phone("+20502221234"))   # Mansoura (050)
        self.assertFalse(is_mobile_phone("+20623331234"))   # Suez (062)
        self.assertFalse(is_mobile_phone("+20643331234"))   # Ismailia (064)
        self.assertFalse(is_mobile_phone("+20653331234"))   # Red Sea (065)
        self.assertFalse(is_mobile_phone("+20663331234"))   # Port Said (066)

    def test_phone_validity_classification(self):
        self.assertEqual(get_phone_validity("+201012345678"), PHONE_VALID)
        self.assertEqual(get_phone_validity("+20133221234"), PHONE_LANDLINE)
        self.assertEqual(get_phone_validity("+20233445566"), PHONE_LANDLINE)
        self.assertEqual(get_phone_validity("123"), PHONE_INVALID)
        self.assertEqual(get_phone_validity(""), PHONE_UNKNOWN)


if __name__ == "__main__":
    unittest.main()

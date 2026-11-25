"""AutoLeadGen V3 — Tests for API schemas, AI Intelligence, and IMAP classifier."""
import unittest
from services.ai_service import AILeadIntelligence, ai_service
from integrations.imap_listener import classify_reply_sentiment


class TestAIService(unittest.TestCase):
    def setUp(self):
        self.ai = AILeadIntelligence()

    def test_classify_restaurant(self):
        res = self.ai.classify_industry("Nile Burger House & Pizza Grill", "Delicious gourmet food and dining delivery")
        self.assertEqual(res, "Restaurants & Food")

    def test_classify_healthcare(self):
        res = self.ai.classify_industry("Al-Shifa Dental Clinic & Surgery", "Specialized doctor for dental implants and medical care")
        self.assertEqual(res, "Healthcare & Medical")

    def test_classify_technology(self):
        res = self.ai.classify_industry("CloudTech Solutions", "Custom software development, SaaS apps and cloud hosting")
        self.assertEqual(res, "Technology & Software")

    def test_data_completeness_scoring(self):
        full_lead = {
            "business_name": "Acme Corp",
            "phone": "+201012345678",
            "email": "contact@acme.com",
            "website": "https://acme.com",
            "latitude": 30.05,
            "longitude": 31.23,
            "city": "Cairo",
        }
        score = self.ai.score_data_completeness(full_lead)
        self.assertEqual(score, 1.0)

        empty_lead = {}
        score_empty = self.ai.score_data_completeness(empty_lead)
        self.assertEqual(score_empty, 0.0)

    def test_extractive_summary(self):
        text = (
            "Acme Solutions is a premier software company based in Cairo. "
            "We build artificial intelligence platforms for enterprise clients across the globe. "
            "Please agree to our privacy policy and cookie settings."
        )
        summary = self.ai.summarize_business(text, max_words=30)
        self.assertIn("Acme Solutions", summary)
        self.assertNotIn("cookie", summary.lower())

    def test_semantic_deduplication(self):
        candidates = [
            {"id": 1, "business_name": "Sephora Perfumes Cairo", "city": "Cairo", "address": "Nasr City"},
            {"id": 2, "business_name": "Sephora Perfumes Branch Cairo", "city": "Cairo", "address": "Nasr City"},
            {"id": 3, "business_name": "Al-Ahly Sports Club", "city": "Giza", "address": "Zamalek"},
        ]
        dups = self.ai.detect_semantic_duplicates(candidates, threshold=0.60)
        self.assertTrue(any((d[0] == 1 and d[1] == 2) for d in dups))


class TestReplySentiment(unittest.TestCase):
    def test_interested_arabic(self):
        self.assertEqual(classify_reply_sentiment("أهلاً بحضرتك، أنا مهتم بعرض الأسعار، برجاء ارسال التفاصيل"), "interested")

    def test_interested_english(self):
        self.assertEqual(classify_reply_sentiment("Yes, we are interested in a demo next week. What's the price?"), "interested")

    def test_not_interested(self):
        self.assertEqual(classify_reply_sentiment("Please unsubscribe me and remove our company from your list."), "not_interested")

    def test_out_of_office(self):
        self.assertEqual(classify_reply_sentiment("I am currently out of office on annual leave until next Monday."), "out_of_office")

    def test_follow_up(self):
        self.assertEqual(classify_reply_sentiment("We are busy right now, please follow up next month."), "follow_up")


if __name__ == "__main__":
    unittest.main()

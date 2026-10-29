import os
import sys
import unittest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app
from backend.model_service import model_service

class TestEndToEndIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_e2e_health_check(self):
        """Verify serving readiness and model loading."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])
        self.assertTrue(data["model_version"].startswith("v3."))

    def test_e2e_single_spam_email_flow(self):
        """Simulate user checking an urgent lottery spam email."""
        payload = {
            "sender": "prize-notification@jackpot-winner.xyz",
            "subject": "Claim your $5,000 cash prize now!",
            "body": "Congratulations winner! Your email was selected in our international lottery promotion. You have won $5,000 cash. This offer expires today and you have 2 hours to claim. Click here to confirm bank account details immediately."
        }
        
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify prediction properties
        self.assertEqual(data["label"], "spam")
        self.assertTrue(data["is_spam"])
        self.assertGreaterEqual(data["spam_probability"], 0.75)
        self.assertGreaterEqual(data["confidence"], 75.0)
        self.assertEqual(data["verdict_title"], "Likely spam")
        self.assertIn("latency_ms", data)
        self.assertGreater(data["latency_ms"], 0.0)
        
        # Verify explainability signals
        reasons = [r["title"] for r in data["flagged_reasons"]]
        self.assertIn("Urgency language", reasons)
        self.assertIn("Suspicious offer", reasons)
        self.assertIn("Call to action", reasons)
        
        # Verify risk breakdown
        breakdown = data["risk_breakdown"]
        self.assertGreater(breakdown["content_signals"], 70)
        self.assertGreater(breakdown["link_safety"], 70)

    def test_e2e_single_legitimate_email_flow(self):
        """Simulate user checking a standard business correspondence email."""
        payload = {
            "sender": "alex.smith@enron.com",
            "subject": "Updated agenda for executive board sync",
            "body": "Hi team, please find attached the reviewed quarterly financial numbers for our division. Overall revenues exceeded expectations by 4.2%. Let me know if you have any questions before the sync tomorrow."
        }
        
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify prediction properties
        self.assertEqual(data["label"], "legitimate")
        self.assertFalse(data["is_spam"])
        self.assertLess(data["spam_probability"], 0.25)
        self.assertEqual(data["verdict_title"], "Likely legitimate")
        self.assertIn("latency_ms", data)
        
        # Verify clean signals
        breakdown = data["risk_breakdown"]
        self.assertLess(breakdown["content_signals"], 30)
        self.assertLess(breakdown["link_safety"], 30)

    def test_e2e_batch_prediction_workflow(self):
        """Simulate batch scanning multiple emails via /predict/batch."""
        batch_payload = {
            "emails": [
                {
                    "sender": "rewards@cash-lottery.xyz",
                    "subject": "You have won $1,000 cash!",
                    "body": "Urgent act now within 2 hours to claim your reward prize."
                },
                {
                    "sender": "director@enron.com",
                    "subject": "Weekly department sync notes",
                    "body": "Please review the attached notes from this morning's team meeting."
                },
                {
                    "sender": "security-alert@verify-account.net",
                    "subject": "Urgent: verify your identity immediately",
                    "body": "Your credentials will expire today unless you click here to log in."
                }
            ]
        }
        
        response = self.client.post("/predict/batch", json=batch_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["predictions"]), 3)
        self.assertGreaterEqual(data["spam_count"], 1)
        self.assertGreaterEqual(data["legitimate_count"], 1)
        self.assertGreater(data["batch_latency_ms"], 0.0)

    def test_e2e_privacy_conscious_audit_logging(self):
        """Verify that recent logs store metadata and snippets, NOT full raw bodies."""
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        history = response.json()["history"]
        self.assertGreater(len(history), 0)
        
        latest_entry = history[0]
        self.assertIn("id", latest_entry)
        self.assertIn("subject_snippet", latest_entry)
        self.assertIn("sender_domain", latest_entry)
        self.assertIn("latency_ms", latest_entry)
        # Assert full raw body text is NOT stored in the entry
        self.assertNotIn("body", latest_entry)
        self.assertNotIn("raw_text", latest_entry)

if __name__ == "__main__":
    unittest.main()


import os
import sys
import unittest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app

class TestFastAPIBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        """GET /health should return 200 and model_loaded: true."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])
        self.assertTrue(data["model_version"].startswith("v3."))

    def test_model_info_endpoint(self):
        """GET /model/info should return valid model parameters and test evaluation results."""
        response = self.client.get("/model/info")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("model_name", data)
        self.assertIn("evaluation_metrics", data)
        self.assertGreaterEqual(data["evaluation_metrics"]["accuracy"], 90.0)
        self.assertEqual(data["quality_gate_status"], "PASSED")

    def test_predict_valid_spam(self):
        """POST /predict should identify clear spam email with high spam_probability."""
        payload = {
            "sender": "claims-alert@global-lottery-award.net",
            "subject": "Claim your cash prize now - $5,000 awaits you!",
            "body": "Congratulations! You have won $5,000 cash. This offer expires today and you have 2 hours to claim. Click here to confirm bank account details immediately."
        }
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["label"], "spam")
        self.assertTrue(data["is_spam"])
        self.assertGreaterEqual(data["spam_probability"], 0.5)
        self.assertGreaterEqual(data["confidence"], 50.0)
        self.assertIn("latency_ms", data)
        self.assertIn("risk_breakdown", data)
        self.assertEqual(len(data["flagged_reasons"]), 4)

    def test_predict_valid_legitimate(self):
        """POST /predict should identify genuine correspondence as legitimate."""
        payload = {
            "sender": "sarah.jenkins@enron.com",
            "subject": "Quarterly report attached - Q3 financial overview",
            "body": "Hi team, please find attached the reviewed quarterly financial numbers for our division. Overall revenues exceeded expectations by 4.2%. Let me know if you have any questions before the executive board sync."
        }
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["label"], "legitimate")
        self.assertFalse(data["is_spam"])
        self.assertLess(data["spam_probability"], 0.5)
        self.assertGreaterEqual(data["confidence"], 50.0)

    def test_predict_empty_input_rejected(self):
        """POST /predict with empty subject and empty body must be rejected."""
        payload = {
            "sender": "test@example.com",
            "subject": "   ",
            "body": ""
        }
        response = self.client.post("/predict", json=payload)
        self.assertIn(response.status_code, [400, 422])

    def test_predict_oversized_input_rejected(self):
        """POST /predict with body exceeding 50,000 characters must be rejected."""
        payload = {
            "sender": "test@example.com",
            "subject": "Oversized test",
            "body": "A" * 50001
        }
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_predict_batch(self):
        """POST /predict/batch should classify multiple emails in one call."""
        payload = {
            "emails": [
                {
                    "sender": "winner@cash-prizes.xyz",
                    "subject": "You won the lottery! Claim $10,000 now",
                    "body": "Urgent act now within 2 hours to claim your free cash prize!"
                },
                {
                    "sender": "colleague@enron.com",
                    "subject": "All-hands meeting schedule",
                    "body": "Hi everyone, the weekly all-hands has been shifted to 4 PM."
                }
            ]
        }
        response = self.client.post("/predict/batch", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["predictions"]), 2)
        self.assertGreaterEqual(data["spam_count"], 1)
        self.assertGreaterEqual(data["legitimate_count"], 1)
        self.assertGreater(data["batch_latency_ms"], 0.0)

    def test_metrics_endpoint(self):
        """GET /metrics should return valid operational counters."""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_predictions", data)
        self.assertIn("spam_ratio_percent", data)
        self.assertIn("p95_latency_ms", data)
        self.assertGreater(data["uptime_seconds"], 0.0)

    def test_monitoring_drift_endpoint(self):
        """GET /api/monitoring/drift should return structured drift metrics."""
        response = self.client.get("/api/monitoring/drift")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("drift_share", data)
        self.assertIn("features_drift_summary", data)

    def test_monitoring_drift_html_report_endpoint(self):
        """GET /api/monitoring/drift/report.html should serve the HTML report."""
        response = self.client.get("/api/monitoring/drift/report.html")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    def test_trigger_monitoring_endpoint(self):
        """POST /api/monitoring/run should run drift check and return metrics."""
        response = self.client.post("/api/monitoring/run", json={"stream": "normal"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("metrics", data)
        self.assertEqual(data["metrics"]["status"], "HEALTHY")

    def test_trigger_retraining_endpoint(self):
        """POST /api/retrain should invoke candidate retraining and return status."""
        response = self.client.post("/api/retrain", json={"force": False})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("retraining", data)
        self.assertIn(data["retraining"]["status"], ["PROMOTED", "REJECTED_QUALITY_GATE_FAILED"])

if __name__ == "__main__":
    unittest.main()


import os
import unittest
import joblib

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/spam_pipeline.joblib"))

class TestSpamPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Train the pipeline first.")
        cls.model = joblib.load(MODEL_PATH)

    def test_model_loading(self):
        """Ensure the fitted pipeline can be loaded and has expected components."""
        self.assertIsNotNone(self.model)
        self.assertTrue(hasattr(self.model, "predict"))
        self.assertTrue(hasattr(self.model, "predict_proba"))
        self.assertIn("tfidf", self.model.named_steps)
        self.assertIn("classifier", self.model.named_steps)

    def test_empty_and_whitespace_input(self):
        """Ensure empty text and whitespace do not crash the pipeline."""
        for empty_val in ["", "   ", "\n\t", "       "]:
            pred = self.model.predict([empty_val])
            proba = self.model.predict_proba([empty_val])
            self.assertEqual(len(pred), 1)
            self.assertIn(pred[0], [0, 1])
            self.assertEqual(len(proba[0]), 2)
            self.assertTrue(0.0 <= proba[0][0] <= 1.0)
            self.assertTrue(0.0 <= proba[0][1] <= 1.0)

    def test_malformed_input(self):
        """Ensure special characters, punctuation-only, and numeric strings work gracefully."""
        malformed_inputs = [
            "!@#$%^&*()_+=-~`",
            "1234567890 99999 0000",
            "???? ..... !!!! ,,,, ;;;",
            "a" * 1000
        ]
        preds = self.model.predict(malformed_inputs)
        probas = self.model.predict_proba(malformed_inputs)
        self.assertEqual(len(preds), len(malformed_inputs))
        self.assertEqual(len(probas), len(malformed_inputs))

    def test_clear_spam_sample(self):
        """Validate that unambiguous spam signals predict spam (class 1)."""
        spam_sample = (
            "Subject: Urgent: Claim your $10,000 lottery cash prize! "
            "Congratulations you have won millions in cash reward! "
            "Act now offer expires today within 2 hours. Click here to confirm bank account details immediately."
        )
        pred = self.model.predict([spam_sample])[0]
        prob = self.model.predict_proba([spam_sample])[0]
        self.assertEqual(pred, 1, f"Expected spam (1), got {pred}")
        self.assertGreaterEqual(prob[1], 0.5, f"Expected spam probability >= 0.5, got {prob[1]}")

    def test_clear_legitimate_sample(self):
        """Validate that standard workplace communication predicts legitimate (class 0)."""
        ham_sample = (
            "Subject: Team meeting notes and Q3 budget sync "
            "Hi everyone, please review the attached minutes from our executive meeting yesterday. "
            "The project milestones are tracking ahead of schedule. Let me know if you have any feedback."
        )
        pred = self.model.predict([ham_sample])[0]
        prob = self.model.predict_proba([ham_sample])[0]
        self.assertEqual(pred, 0, f"Expected ham (0), got {pred}")
        self.assertGreaterEqual(prob[0], 0.5, f"Expected ham probability >= 0.5, got {prob[0]}")

    def test_probability_distribution(self):
        """Ensure probabilities sum to 1.0 within numerical precision."""
        sample = "Reminder for tomorrow's department seminar."
        prob = self.model.predict_proba([sample])[0]
        self.assertAlmostEqual(sum(prob), 1.0, places=4)

if __name__ == "__main__":
    unittest.main()

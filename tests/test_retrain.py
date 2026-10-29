import os
import unittest
import pandas as pd
import json

from src.retrain import validate_and_clean_new_data, retrain_and_evaluate

class TestRetrainingWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_csv = "data/monitoring/test_temp_labels.csv"
        os.makedirs("data/monitoring", exist_ok=True)
        df = pd.DataFrame({
            "text": [
                "Legitimate quarterly financial update from department.",
                "URGENT: Claim $5,000 cash prize instantly!",
                "",  # Empty to test dropping
                "Legitimate quarterly financial update from department."  # Duplicate
            ],
            "label": [0, 1, 0, 0]
        })
        df.to_csv(self.temp_csv, index=False)

    def tearDown(self):
        if os.path.exists(self.temp_csv):
            os.remove(self.temp_csv)

    def test_validation_and_deduplication(self):
        existing_texts = {"already existing baseline document"}
        cleaned_df = validate_and_clean_new_data(self.temp_csv, existing_texts)
        # Should drop the empty row and deduplicate the duplicate
        self.assertEqual(len(cleaned_df), 2)
        self.assertIn("clean_text", cleaned_df.columns)
        self.assertEqual(cleaned_df["label"].tolist(), [0, 1])

    def test_retraining_execution_and_quality_gate(self):
        res = retrain_and_evaluate(new_data_path=self.temp_csv, force_promote=False)
        self.assertIn(res["status"], ["PROMOTED", "REJECTED_QUALITY_GATE_FAILED"])
        self.assertIn("metrics", res)
        self.assertGreater(res["metrics"]["f1_score"], 85.0)
        self.assertGreater(res["metrics"]["accuracy"], 85.0)
        self.assertLess(res["metrics"]["false_positive_rate"], 5.0)

if __name__ == "__main__":
    unittest.main()


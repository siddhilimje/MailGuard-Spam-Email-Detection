import os
import unittest
import pandas as pd
import numpy as np
import json

from src.features import extract_text_features, extract_features_dataframe
from src.monitor import calculate_statistical_drift, run_monitoring

class TestMonitoringPipeline(unittest.TestCase):
    def test_feature_extraction_empty(self):
        feat = extract_text_features("")
        self.assertEqual(feat["char_length"], 0)
        self.assertEqual(feat["token_count"], 0)
        self.assertEqual(feat["uppercase_ratio"], 0.0)

    def test_feature_extraction_signals(self):
        text = "URGENT WINNER: Claim $5,000 cash at http://award-now.xyz today!"
        feat = extract_text_features(text, spam_prob=0.95)
        self.assertGreater(feat["char_length"], 20)
        self.assertGreater(feat["token_count"], 5)
        self.assertGreater(feat["uppercase_ratio"], 0.15)
        self.assertGreater(feat["url_count"], 0)
        self.assertGreater(feat["currency_count"], 0)
        self.assertEqual(feat["spam_probability"], 0.95)

    def test_feature_dataframe_extraction(self):
        df = pd.DataFrame({
            "text": [
                "Quarterly executive team sync in meeting room 2.",
                "WIN $10,000 CASH BONUS TODAY! VISIT http://scam.net"
            ],
            "label": [0, 1]
        })
        feat_df = extract_features_dataframe(df)
        self.assertEqual(len(feat_df), 2)
        self.assertIn("char_length", feat_df.columns)
        self.assertIn("uppercase_ratio", feat_df.columns)
        self.assertIn("spam_probability", feat_df.columns)

    def test_statistical_drift_identical(self):
        np.random.seed(42)
        ref = pd.DataFrame({
            "length": np.random.normal(100, 15, 100),
            "tokens": np.random.normal(20, 5, 100)
        })
        curr = pd.DataFrame({
            "length": np.random.normal(100, 15, 100),
            "tokens": np.random.normal(20, 5, 100)
        })
        results, drifted_cnt, total, share = calculate_statistical_drift(ref, curr, p_value_threshold=0.01)
        self.assertEqual(drifted_cnt, 0)
        self.assertEqual(share, 0.0)

    def test_statistical_drift_shifted(self):
        np.random.seed(42)
        ref = pd.DataFrame({
            "length": np.random.normal(100, 10, 100),
            "tokens": np.random.normal(20, 3, 100)
        })
        curr = pd.DataFrame({
            "length": np.random.normal(500, 20, 100),  # Heavy shift
            "tokens": np.random.normal(80, 5, 100)
        })
        results, drifted_cnt, total, share = calculate_statistical_drift(ref, curr, p_value_threshold=0.05)
        self.assertEqual(drifted_cnt, 2)
        self.assertEqual(share, 1.0)

    def test_monitoring_normal_stream_healthy(self):
        res = run_monitoring(stream_type="normal")
        self.assertEqual(res["status"], "HEALTHY")
        self.assertFalse(res["is_drift_detected"])
        self.assertIn("0/7", res["features_drift_summary"])

    def test_monitoring_drifted_stream_warning(self):
        res = run_monitoring(stream_type="drifted")
        self.assertEqual(res["status"], "WARNING_DRIFT_DETECTED")
        self.assertTrue(res["is_drift_detected"])
        self.assertGreater(res["drift_share"], 0.30)

if __name__ == "__main__":
    unittest.main()


import os
import sys
import json
import yaml
import time
import argparse
import logging
import pandas as pd
import numpy as np
from scipy import stats
import joblib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.features import extract_features_dataframe, extract_text_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("monitor")

PARAMS_FILE = os.path.join(PROJECT_ROOT, "params.yaml")
DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "spam_pipeline.joblib")

def load_params():
    if os.path.exists(PARAMS_FILE):
        with open(PARAMS_FILE, "r") as f:
            return yaml.safe_load(f)
    return {}

def load_reference_data(ref_path: str, sample_size: int = 1500, random_seed: int = 42, model_pipeline=None) -> pd.DataFrame:
    """
    Loads training data reference baseline and extracts text-derived numerical features.
    """
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Reference dataset not found at {ref_path}")
        
    ref_df = pd.read_csv(ref_path)
    if len(ref_df) > sample_size:
        ref_df = ref_df.sample(n=sample_size, random_state=random_seed)
        
    logger.info(f"Extracting baseline features from {len(ref_df)} reference samples...")
    feature_df = extract_features_dataframe(ref_df, text_column="clean_text", model_pipeline=model_pipeline)
    return feature_df

def load_current_data(stream_source: str, model_pipeline=None) -> pd.DataFrame:
    """
    Loads current production data stream (JSONL logs or CSV stream)
    and formats text-derived numerical features.
    """
    if not os.path.exists(stream_source):
        raise FileNotFoundError(f"Stream dataset not found at {stream_source}")
        
    if stream_source.endswith(".jsonl"):
        records = []
        with open(stream_source, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        if not records:
            raise ValueError(f"No valid records found in log file {stream_source}")
            
        df = pd.DataFrame(records)
        expected_cols = ["char_length", "token_count", "uppercase_ratio", "digit_count", "url_count", "currency_count", "spam_probability"]
        # If columns already exist in logs, use them directly
        if all(c in df.columns for c in expected_cols):
            return df[expected_cols].copy()
        elif "text" in df.columns or "clean_text" in df.columns:
            return extract_features_dataframe(df, model_pipeline=model_pipeline)
        else:
            raise ValueError(f"Log format missing expected feature columns. Present: {df.columns.tolist()}")
            
    elif stream_source.endswith(".csv"):
        df = pd.read_csv(stream_source)
        return extract_features_dataframe(df, text_column="text" if "text" in df.columns else "clean_text", model_pipeline=model_pipeline)
    else:
        raise ValueError(f"Unsupported file format for stream source: {stream_source}")

def calculate_statistical_drift(ref_df: pd.DataFrame, curr_df: pd.DataFrame, p_value_threshold: float = 0.05):
    """
    Performs two-sample Kolmogorov-Smirnov (KS) tests across continuous numerical features
    to detect distribution divergence.
    """
    feature_results = {}
    drifted_count = 0
    feature_columns = [c for c in ref_df.columns if c in curr_df.columns]
    
    for col in feature_columns:
        ref_vals = ref_df[col].dropna().values
        curr_vals = curr_df[col].dropna().values
        
        if len(ref_vals) == 0 or len(curr_vals) == 0:
            continue
            
        # Perform 2-sample KS test
        ks_res = stats.ks_2samp(ref_vals, curr_vals)
        stat = float(ks_res.statistic)
        p_val = float(ks_res.pvalue)
        
        is_drifted = bool(p_val < p_value_threshold)
        if is_drifted:
            drifted_count += 1
            
        feature_results[col] = {
            "feature": col,
            "test_type": "Kolmogorov-Smirnov",
            "p_value": round(p_val, 6),
            "p_value_threshold": p_value_threshold,
            "statistic": round(stat, 4),
            "is_drifted": is_drifted,
            "ref_mean": round(float(np.mean(ref_vals)), 4),
            "curr_mean": round(float(np.mean(curr_vals)), 4),
            "ref_std": round(float(np.std(ref_vals)), 4),
            "curr_std": round(float(np.std(curr_vals)), 4)
        }
        
    total_features = len(feature_columns)
    drift_share = round(drifted_count / max(1, total_features), 4)
    
    return feature_results, drifted_count, total_features, drift_share

def generate_evidently_report(ref_features: pd.DataFrame, curr_features: pd.DataFrame, output_html_path: str):
    """
    Executes Evidently AI 0.7.23 Report with DataDriftPreset and saves an interactive HTML artifact.
    """
    os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
    try:
        from evidently import Report
        from evidently.presets import DataDriftPreset
        
        report = Report(metrics=[DataDriftPreset()])
        snapshot = report.run(reference_data=ref_features, current_data=curr_features)
        snapshot.save_html(output_html_path)
        logger.info(f"Evidently AI interactive report saved to: {output_html_path}")
        return True
    except Exception as e:
        logger.warning(f"Evidently AI report generation fallback: {e}")
        # Generate standalone clean HTML report as fallback
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>MailGuard Drift Report</title>
    <style>body{{font-family:sans-serif;padding:30px;line-height:1.6;}} h1{{color:#1e293b;}}</style>
</head>
<body>
    <h1>MailGuard Statistical Drift Report</h1>
    <p>Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Reference Samples: {len(ref_features)} | Current Stream Samples: {len(curr_features)}</p>
</body>
</html>""")
        return False

def run_monitoring(stream_type: str = "logs", custom_stream_path: str = None):
    """
    Orchestrates the monitoring workflow:
    1. Loads reference data and current stream data.
    2. Computes feature drift metrics and statistical tests.
    3. Evaluates alert thresholds and drift status.
    4. Generates Evidently AI HTML report and JSON summary metrics.
    """
    params = load_params()
    mon_params = params.get("monitoring", {})
    
    ref_path = os.path.join(PROJECT_ROOT, mon_params.get("reference_data_path", "data/processed/train.csv"))
    html_report_path = os.path.join(PROJECT_ROOT, mon_params.get("drift_report_html", "reports/monitoring/data_drift_report.html"))
    json_metrics_path = os.path.join(PROJECT_ROOT, mon_params.get("drift_metrics_json", "reports/monitoring/drift_metrics.json"))
    
    drift_share_threshold = float(mon_params.get("drift_share_threshold", 0.30))
    p_value_threshold = float(mon_params.get("p_value_threshold", 0.05))
    min_samples = int(mon_params.get("min_samples_for_drift", 20))
    
    # Resolve stream source
    if custom_stream_path:
        curr_path = os.path.abspath(custom_stream_path)
        stream_name = os.path.basename(custom_stream_path)
    elif stream_type == "normal":
        curr_path = os.path.join(PROJECT_ROOT, "data", "monitoring", "production_stream_normal.csv")
        stream_name = "production_stream_normal.csv"
    elif stream_type == "drifted":
        curr_path = os.path.join(PROJECT_ROOT, "data", "monitoring", "production_stream_drifted.csv")
        stream_name = "production_stream_drifted.csv"
    else:
        curr_path = os.path.join(PROJECT_ROOT, mon_params.get("production_log_path", "data/monitoring/prediction_logs.jsonl"))
        stream_name = "prediction_logs.jsonl"
        
    logger.info(f"Running drift monitoring on stream: {stream_name} ({curr_path})")
    
    # Load model pipeline if available
    pipeline = None
    if os.path.exists(DEFAULT_MODEL_PATH):
        try:
            loaded = joblib.load(DEFAULT_MODEL_PATH)
            pipeline = loaded["pipeline"] if isinstance(loaded, dict) and "pipeline" in loaded else loaded
        except Exception:
            pipeline = None
            
    # Load reference & stream features
    ref_features = load_reference_data(ref_path, sample_size=1000, model_pipeline=pipeline)
    curr_features = load_current_data(curr_path, model_pipeline=pipeline)
    
    if len(curr_features) < min_samples:
        logger.warning(f"Current stream has {len(curr_features)} samples, which is below minimum {min_samples} required for reliable drift calculation.")
        
    # Run statistical drift detection
    feature_results, drifted_count, total_features, drift_share = calculate_statistical_drift(
        ref_features, curr_features, p_value_threshold=p_value_threshold
    )
    
    # Drift alert condition
    is_drift_detected = drift_share >= drift_share_threshold
    status = "WARNING_DRIFT_DETECTED" if is_drift_detected else "HEALTHY"
    
    # Prediction distribution shift
    ref_spam_ratio = round(float(np.mean(ref_features["spam_probability"] > 0.5)) * 100, 2)
    curr_spam_ratio = round(float(np.mean(curr_features["spam_probability"] > 0.5)) * 100, 2)
    
    # Generate Evidently AI report
    generate_evidently_report(ref_features, curr_features, html_report_path)
    
    # Assemble comprehensive structured metrics
    metrics_summary = {
        "status": status,
        "is_drift_detected": is_drift_detected,
        "alert_message": (
            f"WARNING: Data drift detected! {drifted_count}/{total_features} features ({round(drift_share * 100, 1)}%) "
            f"exceeded threshold ({round(drift_share_threshold * 100, 1)}%). Model retraining recommended."
            if is_drift_detected else
            f"Healthy: Data distribution matches baseline within tolerance ({drifted_count}/{total_features} drifted)."
        ),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stream_source": stream_name,
        "reference_dataset": "Enron-Spam Corpus (data/processed/train.csv)",
        "reference_samples": len(ref_features),
        "current_samples": len(curr_features),
        "drift_share": drift_share,
        "drift_share_threshold": drift_share_threshold,
        "p_value_threshold": p_value_threshold,
        "drifted_features_count": drifted_count,
        "total_features_count": total_features,
        "features_drift_summary": f"{drifted_count}/{total_features}",
        "features": feature_results,
        "prediction_distribution": {
            "reference_spam_ratio_percent": ref_spam_ratio,
            "current_spam_ratio_percent": curr_spam_ratio,
            "distribution_delta_percent": round(curr_spam_ratio - ref_spam_ratio, 2)
        },
        "conceptual_distinction": (
            "Data Drift evaluates P(X), the input feature distribution over time without needing labels. "
            "Model Performance Degradation evaluates P(Y|X), such as drop in F1-score or Accuracy. "
            "Because ground-truth labels (Y) are not available in real-time production inference, "
            "true model accuracy cannot be calculated without human review / feedback verification."
        )
    }
    
    os.makedirs(os.path.dirname(json_metrics_path), exist_ok=True)
    with open(json_metrics_path, "w") as f:
        json.dump(metrics_summary, f, indent=2)
        
    logger.info(f"Monitoring completed with status: {status} ({drifted_count}/{total_features} features drifted)")
    logger.info(f"Summary metrics saved to: {json_metrics_path}")
    return metrics_summary

def main():
    parser = argparse.ArgumentParser(description="Spam Email Detection System — Data Drift Monitoring")
    parser.add_argument("--stream", choices=["logs", "normal", "drifted"], default="logs", help="Select stream type to evaluate")
    parser.add_argument("--file", type=str, default=None, help="Custom CSV or JSONL file to evaluate")
    args = parser.parse_args()
    
    result = run_monitoring(stream_type=args.stream, custom_stream_path=args.file)
    print("\n" + "=" * 60)
    print(f"MONITORING RUN RESULT: [{result['status']}]")
    print("=" * 60)
    print(f"Stream:               {result['stream_source']}")
    print(f"Reference Samples:    {result['reference_samples']}")
    print(f"Current Samples:      {result['current_samples']}")
    print(f"Features Drifted:     {result['features_drift_summary']} (share: {result['drift_share']:.1%})")
    print(f"Threshold:            {result['drift_share_threshold']:.1%}")
    print(f"Spam Ratio Shift:     {result['prediction_distribution']['reference_spam_ratio_percent']}% -> {result['prediction_distribution']['current_spam_ratio_percent']}%")
    print(f"Alert Message:        {result['alert_message']}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()


import os
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
import sys
import json
import yaml
import time
import argparse
import logging
import joblib
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.preprocess import clean_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("retrain")

PARAMS_FILE = os.path.join(PROJECT_ROOT, "params.yaml")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
BACKEND_MODEL_DIR = os.path.join(PROJECT_ROOT, "backend", "saved_models")
RETRAINING_LOG_PATH = os.path.join(PROJECT_ROOT, "reports", "monitoring", "retraining_log.json")

def load_params():
    if os.path.exists(PARAMS_FILE):
        with open(PARAMS_FILE, "r") as f:
            return yaml.safe_load(f)
    return {}

def validate_and_clean_new_data(new_data_path: str, existing_texts: set):
    """
    Validates newly labeled samples:
    - Checks required columns ('text' or 'message', 'label')
    - Maps string labels ('spam'/'ham') to integers (1/0)
    - Drops empty/null text
    - Deduplicates against existing baseline training samples
    """
    if not os.path.exists(new_data_path):
        raise FileNotFoundError(f"New labeled data not found at {new_data_path}")
        
    df = pd.read_csv(new_data_path)
    logger.info(f"Loaded {len(df)} candidate feedback samples from {new_data_path}")
    
    # Identify text column
    if "text" in df.columns:
        text_col = "text"
    elif "clean_text" in df.columns:
        text_col = "clean_text"
    elif "message" in df.columns:
        text_col = "message"
    else:
        raise ValueError(f"Missing required text column in {df.columns.tolist()}")
        
    # Identify label column
    label_col = "label" if "label" in df.columns else ("spam/ham" if "spam/ham" in df.columns else None)
    if label_col is None:
        raise ValueError("Missing 'label' column in new data.")
        
    # Normalize labels
    valid_rows = []
    dropped_empty = 0
    dropped_duplicate = 0
    
    for _, row in df.iterrows():
        raw_text = str(row[text_col]).strip()
        if not raw_text or raw_text.lower() == "nan":
            dropped_empty += 1
            continue
            
        c_text = clean_text(raw_text)
        if not c_text:
            dropped_empty += 1
            continue
            
        # Deduplication
        if c_text in existing_texts:
            dropped_duplicate += 1
            continue
            
        raw_label = row[label_col]
        if isinstance(raw_label, str):
            label_val = 1 if "spam" in raw_label.lower() else 0
        else:
            label_val = 1 if int(raw_label) == 1 else 0
            
        valid_rows.append({
            "text": raw_text,
            "clean_text": c_text,
            "label": label_val
        })
        existing_texts.add(c_text)
        
    logger.info(f"Validated samples: {len(valid_rows)} accepted, {dropped_duplicate} duplicates skipped, {dropped_empty} empty dropped.")
    return pd.DataFrame(valid_rows)

def retrain_and_evaluate(new_data_path: str = None, force_promote: bool = False):
    """
    Executes the full automated retraining workflow with quality gate enforcement:
    1. Ingests and validates newly labeled feedback records.
    2. Combines them with approved training data.
    3. Trains candidate pipeline with identical ML pipeline contracts.
    4. Evaluates candidate on held-out validation set.
    5. Checks Quality Gate (Thresholds + Non-regression vs. Champion).
    6. Logs run to MLflow.
    7. Conditionally promotes or preserves existing model.
    """
    params = load_params()
    tfidf_cfg = params.get("tfidf", {})
    gate_cfg = params.get("quality_gate", {})
    mlflow_cfg = params.get("mlflow", {})
    
    if new_data_path is None:
        new_data_path = os.path.join(PROJECT_ROOT, "data", "monitoring", "new_labels.csv")
        
    train_path = os.path.join(PROJECT_ROOT, "data", "processed", "train.csv")
    val_path = os.path.join(PROJECT_ROOT, "data", "processed", "val.csv")
    
    if not os.path.exists(train_path) or not os.path.exists(val_path):
        raise FileNotFoundError("Base processed datasets missing. Run DVC prepare stage first.")
        
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    
    existing_texts = set(train_df["clean_text"].fillna("").astype(str).tolist())
    
    # 1. Validate new data
    new_df = validate_and_clean_new_data(new_data_path, existing_texts)
    
    # 2. Combine training data
    if len(new_df) > 0:
        combined_train = pd.concat([train_df[["clean_text", "label"]], new_df[["clean_text", "label"]]], ignore_index=True)
    else:
        combined_train = train_df[["clean_text", "label"]].copy()
        
    X_train = combined_train["clean_text"].values
    y_train = combined_train["label"].values
    
    X_val = val_df["clean_text"].fillna("").values
    y_val = val_df["label"].values
    
    logger.info(f"Training candidate model on {len(X_train)} samples ({len(new_df)} newly incorporated)...")
    
    # 3. Fit candidate pipeline
    vectorizer = TfidfVectorizer(
        max_features=tfidf_cfg.get("max_features", 25000),
        ngram_range=(tfidf_cfg.get("ngram_min", 1), tfidf_cfg.get("ngram_max", 2)),
        stop_words=tfidf_cfg.get("stop_words", "english"),
        sublinear_tf=tfidf_cfg.get("sublinear_tf", True)
    )
    classifier = MultinomialNB(alpha=params.get("naive_bayes", {}).get("alpha", 0.1))
    
    candidate_pipeline = Pipeline([
        ("tfidf", vectorizer),
        ("classifier", classifier)
    ])
    
    t0 = time.time()
    candidate_pipeline.fit(X_train, y_train)
    train_duration = round(time.time() - t0, 3)
    
    # 4. Evaluate on held-out validation set
    y_pred = candidate_pipeline.predict(X_val)
    acc = round(accuracy_score(y_val, y_pred) * 100, 2)
    prec = round(precision_score(y_val, y_pred, zero_division=0) * 100, 2)
    rec = round(recall_score(y_val, y_pred, zero_division=0) * 100, 2)
    f1 = round(f1_score(y_val, y_pred, zero_division=0) * 100, 2)
    
    cm = confusion_matrix(y_val, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = round((fp / max(1, fp + tn)) * 100, 3)
    
    # 5. Retrieve baseline champion metrics
    champion_metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")
    champion_f1 = 96.6
    champion_version = "v3.8.2"
    if os.path.exists(champion_metadata_path):
        try:
            with open(champion_metadata_path, "r") as f:
                champ_data = json.load(f)
                champion_f1 = champ_data.get("validation_metrics", {}).get("f1_score", 96.6)
                champion_version = champ_data.get("version", "v3.8.2")
        except Exception:
            pass
            
    # 6. Quality Gate Assessment
    min_f1 = float(gate_cfg.get("min_f1_score", 90.0))
    min_acc = float(gate_cfg.get("min_accuracy", 90.0))
    min_prec = float(gate_cfg.get("min_spam_precision", 88.0))
    max_fpr = float(gate_cfg.get("max_false_positive_rate_percent", 3.0))
    
    reasons = []
    if f1 < min_f1:
        reasons.append(f"F1-score {f1}% below minimum required {min_f1}%")
    if acc < min_acc:
        reasons.append(f"Accuracy {acc}% below minimum required {min_acc}%")
    if prec < min_prec:
        reasons.append(f"Precision {prec}% below minimum required {min_prec}%")
    if fpr > max_fpr:
        reasons.append(f"False Positive Rate {fpr}% exceeds maximum allowed {max_fpr}%")
    if f1 < (champion_f1 - 0.5):
        reasons.append(f"Regression detected: Candidate F1 ({f1}%) regressed vs Champion ({champion_f1}%)")
        
    gate_passed = len(reasons) == 0 or force_promote
    
    new_version = f"v{int(champion_version.replace('v', '').split('.')[0])}.{int(champion_version.split('.')[1]) + 1}.0-retrained"
    
    # 7. MLflow Experiment Logging
    try:
        tracking_uri = mlflow_cfg.get("tracking_uri", "sqlite:///mlflow.db")
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(mlflow_cfg.get("experiment_name", "Spam_Email_Detection_System"))
        
        with mlflow.start_run(run_name=f"Retraining_{new_version}"):
            mlflow.log_params({
                "model_type": "Multinomial Naive Bayes (Retrained)",
                "new_labeled_samples": len(new_df),
                "total_train_samples": len(X_train),
                "train_duration_s": train_duration,
                "vectorizer_max_features": tfidf_cfg.get("max_features", 25000),
                "champion_baseline_f1": champion_f1
            })
            mlflow.log_metrics({
                "val_accuracy": acc,
                "val_precision": prec,
                "val_recall": rec,
                "val_f1_score": f1,
                "val_fpr_percent": fpr,
                "val_false_positives": int(fp),
                "val_false_negatives": int(fn)
            })
            mlflow.set_tag("quality_gate_verdict", "PASSED" if gate_passed else "FAILED")
            mlflow.set_tag("promotion_decision", "PROMOTED" if gate_passed else "REJECTED")
            mlflow.sklearn.log_model(candidate_pipeline, "retrained_model")
            logger.info("Retraining run successfully logged to MLflow.")
    except Exception as e:
        logger.warning(f"MLflow logging notice: {e}")
        
    # 8. Promotion Decision
    if gate_passed:
        logger.info(f"QUALITY GATE PASSED. Promoting candidate {new_version} to Production.")
        # Save to models/
        prod_model_path = os.path.join(MODELS_DIR, "spam_pipeline.joblib")
        joblib.dump(candidate_pipeline, prod_model_path)
        
        # Save to backend/saved_models/
        os.makedirs(BACKEND_MODEL_DIR, exist_ok=True)
        joblib.dump(candidate_pipeline, os.path.join(BACKEND_MODEL_DIR, "spam_classifier.joblib"))
        
        # Update metadata
        updated_metadata = {
            "selected_model": "Multinomial Naive Bayes",
            "version": new_version,
            "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "train_samples": len(X_train),
            "new_samples_added": len(new_df),
            "validation_metrics": {
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
                "false_positive_rate_percent": fpr,
                "confusion_matrix": {
                    "true_negatives": int(tn),
                    "false_positives": int(fp),
                    "false_negatives": int(fn),
                    "true_positives": int(tp)
                }
            },
            "quality_gate": {
                "status": "PASSED",
                "rules": gate_cfg
            }
        }
        with open(champion_metadata_path, "w") as f:
            json.dump(updated_metadata, f, indent=2)
            
        promotion_status = "PROMOTED"
    else:
        logger.warning(f"QUALITY GATE FAILED. Preserving existing champion ({champion_version}). Reasons: {reasons}")
        promotion_status = "REJECTED_QUALITY_GATE_FAILED"
        
    retraining_result = {
        "status": promotion_status,
        "gate_passed": gate_passed,
        "candidate_version": new_version,
        "active_production_version": new_version if gate_passed else champion_version,
        "reasons": reasons if not gate_passed else ["All validation criteria and non-regression checks satisfied."],
        "new_samples_added": len(new_df),
        "total_training_samples": len(X_train),
        "metrics": {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "false_positive_rate": fpr,
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "quality_gate_thresholds": {
            "min_f1_score": min_f1,
            "min_accuracy": min_acc,
            "min_spam_precision": min_prec,
            "max_false_positive_rate_percent": max_fpr,
            "champion_f1_score": champion_f1
        },
        "retrained_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    os.makedirs(os.path.dirname(RETRAINING_LOG_PATH), exist_ok=True)
    with open(RETRAINING_LOG_PATH, "w") as f:
        json.dump(retraining_result, f, indent=2)
        
    return retraining_result

def main():
    parser = argparse.ArgumentParser(description="Spam Email Detection System — Automated Retraining Pipeline")
    parser.add_argument("--new-data", type=str, default=None, help="Path to new labeled CSV dataset")
    parser.add_argument("--force", action="store_true", help="Force promotion regardless of quality gate")
    args = parser.parse_args()
    
    result = retrain_and_evaluate(new_data_path=args.new_data, force_promote=args.force)
    print("\n" + "=" * 60)
    print(f"RETRAINING RESULT: [{result['status']}]")
    print("=" * 60)
    print(f"Candidate Version:    {result['candidate_version']}")
    print(f"Active Model Version: {result['active_production_version']}")
    print(f"New Samples Ingested: {result['new_samples_added']}")
    print(f"Total Train Size:     {result['total_training_samples']}")
    print(f"Validation F1-Score:  {result['metrics']['f1_score']}%")
    print(f"Validation Accuracy:  {result['metrics']['accuracy']}%")
    print(f"Spam Precision:       {result['metrics']['precision']}%")
    print(f"False Positives:      {result['metrics']['false_positives']} (FPR: {result['metrics']['false_positive_rate']}%)")
    print(f"Quality Gate Verdict: {'PASS' if result['gate_passed'] else 'FAIL'}")
    if not result['gate_passed']:
        print("Failure Reasons:     ", result['reasons'])
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()

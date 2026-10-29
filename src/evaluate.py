import os
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
import json
import yaml
import time
import joblib
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score
)
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PARAMS_FILE = os.path.join(PROJECT_ROOT, "params.yaml")
CANDIDATE_PATH = os.path.join(PROJECT_ROOT, "models", "candidate_pipeline.joblib")
PROMOTED_PATH = os.path.join(PROJECT_ROOT, "models", "spam_pipeline.joblib")
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend", "saved_models", "spam_classifier.joblib")
RESULTS_PATH = os.path.join(PROJECT_ROOT, "models", "evaluation_results.json")
METADATA_PATH = os.path.join(PROJECT_ROOT, "models", "model_metadata.json")

def load_params():
    with open(PARAMS_FILE, "r") as f:
        return yaml.safe_load(f)

def run_evaluation_and_quality_gate():
    params = load_params()
    ds_params = params.get("dataset", {})
    gate_params = params.get("quality_gate", {})
    mlflow_params = params.get("mlflow", {})
    
    test_path = os.path.join(PROJECT_ROOT, ds_params.get("processed_dir", "data/processed"), "test.csv")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test dataset missing at {test_path}")
    if not os.path.exists(CANDIDATE_PATH):
        raise FileNotFoundError(f"Candidate model pipeline missing at {CANDIDATE_PATH}")
        
    logger.info(f"Loading candidate pipeline from {CANDIDATE_PATH}...")
    pipeline = joblib.load(CANDIDATE_PATH)
    
    logger.info(f"Loading held-out test dataset from {test_path}...")
    test_df = pd.read_csv(test_path)
    test_df["clean_text"] = test_df["clean_text"].fillna("")
    
    X_test, y_test = test_df["clean_text"], test_df["label"]
    total_samples = len(y_test)
    
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else None
    
    acc = accuracy_score(y_test, y_pred)
    spam_prec = precision_score(y_test, y_pred, pos_label=1, zero_division=0)
    spam_rec = recall_score(y_test, y_pred, pos_label=1, zero_division=0)
    spam_f1 = f1_score(y_test, y_pred, pos_label=1, zero_division=0)
    
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    roc_auc = roc_auc_score(y_test, y_prob) if y_prob is not None else None
    
    test_metrics = {
        "accuracy": round(float(acc) * 100, 2),
        "spam_precision": round(float(spam_prec) * 100, 2),
        "spam_recall": round(float(spam_rec) * 100, 2),
        "spam_f1_score": round(float(spam_f1) * 100, 2),
        "roc_auc": round(float(roc_auc) * 100, 2) if roc_auc is not None else None,
        "false_positive_rate_percent": round(fpr * 100, 3),
        "false_negative_rate_percent": round(fnr * 100, 3),
        "true_positives": int(tp),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn)
    }
    
    # -------------------------------------------------------------
    # MODEL QUALITY GATE VERIFICATION
    # -------------------------------------------------------------
    logger.info("Verifying Model Quality Gate thresholds...")
    min_f1 = gate_params.get("min_f1_score", 90.0)
    min_acc = gate_params.get("min_accuracy", 90.0)
    min_prec = gate_params.get("min_spam_precision", 88.0)
    max_fpr = gate_params.get("max_false_positive_rate_percent", 3.0)
    
    gate_checks = [
        ("F1-Score", test_metrics["spam_f1_score"] >= min_f1, f"{test_metrics['spam_f1_score']}% >= {min_f1}%"),
        ("Accuracy", test_metrics["accuracy"] >= min_acc, f"{test_metrics['accuracy']}% >= {min_acc}%"),
        ("Spam Precision", test_metrics["spam_precision"] >= min_prec, f"{test_metrics['spam_precision']}% >= {min_prec}%"),
        ("False Positive Rate", test_metrics["false_positive_rate_percent"] <= max_fpr, f"{test_metrics['false_positive_rate_percent']}% <= {max_fpr}%")
    ]
    
    gate_passed = True
    gate_summary = {}
    for name, passed, detail in gate_checks:
        status_str = "PASS" if passed else "FAIL"
        logger.info(f"  • [{status_str}] {name}: {detail}")
        gate_summary[name] = {"passed": passed, "detail": detail}
        if not passed:
            gate_passed = False
            
    # Guard against replacing a better model with a worse model
    if os.path.exists(RESULTS_PATH):
        try:
            with open(RESULTS_PATH, "r") as f:
                prev_results = json.load(f)
                prev_f1 = prev_results.get("spam_class_metrics", {}).get("f1_score", 0.0)
                if test_metrics["spam_f1_score"] < (prev_f1 - 2.0):
                    logger.error(f"Quality gate rejected regression: Candidate F1 ({test_metrics['spam_f1_score']}%) is worse than existing ({prev_f1}%)")
                    gate_passed = False
                    gate_summary["Non-regression check"] = {"passed": False, "detail": f"{test_metrics['spam_f1_score']}% < {prev_f1}%"}
        except Exception:
            pass

    if not gate_passed:
        logger.error("MODEL QUALITY GATE FAILED! Model promotion halted.")
        raise ValueError("Model failed the Quality Gate requirements. Evaluation aborted.")
        
    logger.info(">>> MODEL QUALITY GATE PASSED! Promoting candidate model to Champion @production...")
    
    # -------------------------------------------------------------
    # MODEL PROMOTION
    # -------------------------------------------------------------
    # Save Promoted Pipeline
    joblib.dump(pipeline, PROMOTED_PATH)
    logger.info(f"Promoted champion model saved to {PROMOTED_PATH}")
    
    # Sync with Backend Serving store
    os.makedirs(os.path.dirname(BACKEND_PATH), exist_ok=True)
    joblib.dump({
        "pipeline": pipeline,
        "version": "v3.8.2",
        "metrics": test_metrics,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }, BACKEND_PATH)
    logger.info(f"Synchronized promoted model to {BACKEND_PATH}")
    
    # -------------------------------------------------------------
    # MLFLOW EVALUATION & REGISTRATION
    # -------------------------------------------------------------
    tracking_uri = mlflow_params.get("tracking_uri", "sqlite:///mlflow.db")
    experiment_name = mlflow_params.get("experiment_name", "Spam_Email_Detection_System")
    reg_model_name = mlflow_params.get("registered_model_name", "MailGuard_Spam_Classifier")
    
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run(run_name="Champion_Promotion_And_Evaluation") as run:
        mlflow.log_params({
            "stage": "Production",
            "evaluated_dataset": "Enron_HeldOut_Test",
            "test_sample_count": total_samples
        })
        
        mlflow.log_metrics({
            "test_accuracy": test_metrics["accuracy"],
            "test_spam_precision": test_metrics["spam_precision"],
            "test_spam_recall": test_metrics["spam_recall"],
            "test_spam_f1_score": test_metrics["spam_f1_score"],
            "test_roc_auc": test_metrics["roc_auc"] if test_metrics["roc_auc"] else 0.0,
            "false_positive_rate_percent": test_metrics["false_positive_rate_percent"],
            "false_negative_rate_percent": test_metrics["false_negative_rate_percent"]
        })
        
        # Log model artifact to MLflow
        mlflow.sklearn.log_model(
            sk_model=pipeline,
            artifact_path="champion_model",
            registered_model_name=reg_model_name
        )
        logger.info(f"Model successfully registered in MLflow Model Registry as '{reg_model_name}'")
        
    # Write Final evaluation report
    report = {
        "evaluation_dataset": "Enron-Spam Held-out Test Split",
        "test_samples": total_samples,
        "quality_gate": {
            "status": "PASSED",
            "checks": gate_summary
        },
        "overall_accuracy": test_metrics["accuracy"],
        "roc_auc": test_metrics["roc_auc"],
        "spam_class_metrics": {
            "precision": test_metrics["spam_precision"],
            "recall": test_metrics["spam_recall"],
            "f1_score": test_metrics["spam_f1_score"]
        },
        "confusion_matrix": {
            "true_negatives": test_metrics["true_negatives"],
            "false_positives": test_metrics["false_positives"],
            "false_negatives": test_metrics["false_negatives"],
            "true_positives": test_metrics["true_positives"]
        },
        "error_rates": {
            "false_positive_rate_percent": test_metrics["false_positive_rate_percent"],
            "false_negative_rate_percent": test_metrics["false_negative_rate_percent"]
        },
        "model_version": "v3.8.2",
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(RESULTS_PATH, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved evaluation results to {RESULTS_PATH}")
    
    print("\n" + "=" * 65)
    print("      CHAMPION EVALUATION & QUALITY GATE SUMMARY")
    print("=" * 65)
    print(f"Overall Accuracy      : {test_metrics['accuracy']}%")
    print(f"Spam Precision        : {test_metrics['spam_precision']}%")
    print(f"Spam Recall           : {test_metrics['spam_recall']}%")
    print(f"Spam F1-Score         : {test_metrics['spam_f1_score']}%")
    print(f"False Positive Rate   : {test_metrics['false_positive_rate_percent']}% (Legit marked spam: {tp})")
    print(f"Quality Gate Status   : PASSED")
    print(f"Registered Model Name : {reg_model_name}")
    print("=" * 65 + "\n")
    return report

if __name__ == "__main__":
    run_evaluation_and_quality_gate()

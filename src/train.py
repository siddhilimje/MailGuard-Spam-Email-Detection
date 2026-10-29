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
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PARAMS_FILE = os.path.join(PROJECT_ROOT, "params.yaml")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

def load_params():
    with open(PARAMS_FILE, "r") as f:
        return yaml.safe_load(f)

def load_data_splits(processed_dir: str):
    train_path = os.path.join(processed_dir, "train.csv")
    val_path = os.path.join(processed_dir, "val.csv")
    
    if not os.path.exists(train_path) or not os.path.exists(val_path):
        raise FileNotFoundError(f"Missing processed data at {train_path} or {val_path}")
        
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    
    train_df["clean_text"] = train_df["clean_text"].fillna("")
    val_df["clean_text"] = val_df["clean_text"].fillna("")
    
    return train_df, val_df

def evaluate_pipeline(pipeline: Pipeline, X_val, y_val):
    y_pred = pipeline.predict(X_val)
    acc = accuracy_score(y_val, y_pred)
    prec = precision_score(y_val, y_pred, zero_division=0)
    rec = recall_score(y_val, y_pred, zero_division=0)
    f1 = f1_score(y_val, y_pred, zero_division=0)
    cm = confusion_matrix(y_val, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    return {
        "accuracy": round(float(acc) * 100, 2),
        "precision": round(float(prec) * 100, 2),
        "recall": round(float(rec) * 100, 2),
        "f1_score": round(float(f1) * 100, 2),
        "true_positives": int(tp),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(y_val, y_pred, output_dict=True)
    }

def train_and_track():
    params = load_params()
    ds_params = params.get("dataset", {})
    tfidf_params = params.get("tfidf", {})
    lr_params = params.get("logistic_regression", {})
    nb_params = params.get("naive_bayes", {})
    mlflow_params = params.get("mlflow", {})
    
    processed_dir = os.path.join(PROJECT_ROOT, ds_params.get("processed_dir", "data/processed"))
    train_df, val_df = load_data_splits(processed_dir)
    
    X_train, y_train = train_df["clean_text"], train_df["label"]
    X_val, y_val = val_df["clean_text"], val_df["label"]
    
    # Configure MLflow
    tracking_uri = mlflow_params.get("tracking_uri", "sqlite:///mlflow.db")
    experiment_name = mlflow_params.get("experiment_name", "Spam_Email_Detection_System")
    
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    logger.info(f"MLflow initialized. Tracking URI: {tracking_uri}, Experiment: {experiment_name}")
    
    tfidf_ngram = (tfidf_params.get("ngram_min", 1), tfidf_params.get("ngram_max", 2))
    
    # -------------------------------------------------------------
    # RUN 1: Baseline Multinomial Naive Bayes
    # -------------------------------------------------------------
    logger.info("Training Model 1: Multinomial Naive Bayes (Baseline)...")
    with mlflow.start_run(run_name="Baseline_MultinomialNB"):
        mlflow.log_param("model_family", "MultinomialNB")
        mlflow.log_param("alpha", nb_params.get("alpha", 0.1))
        mlflow.log_param("tfidf_max_features", tfidf_params.get("max_features", 25000))
        mlflow.log_param("tfidf_ngram_range", str(tfidf_ngram))
        mlflow.log_param("tfidf_sublinear_tf", tfidf_params.get("sublinear_tf", True))
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("val_samples", len(X_val))
        mlflow.log_param("random_seed", ds_params.get("random_seed", 42))
        
        nb_pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                max_features=tfidf_params.get("max_features", 25000),
                ngram_range=tfidf_ngram,
                stop_words=tfidf_params.get("stop_words", "english"),
                sublinear_tf=tfidf_params.get("sublinear_tf", True)
            )),
            ("classifier", MultinomialNB(alpha=nb_params.get("alpha", 0.1)))
        ])
        
        nb_pipeline.fit(X_train, y_train)
        nb_metrics = evaluate_pipeline(nb_pipeline, X_val, y_val)
        
        mlflow.log_metric("val_accuracy", nb_metrics["accuracy"])
        mlflow.log_metric("val_precision", nb_metrics["precision"])
        mlflow.log_metric("val_recall", nb_metrics["recall"])
        mlflow.log_metric("val_f1_score", nb_metrics["f1_score"])
        mlflow.log_metric("val_false_positives", nb_metrics["false_positives"])
        mlflow.log_metric("val_false_negatives", nb_metrics["false_negatives"])
        
        # Save temp artifact
        os.makedirs(MODELS_DIR, exist_ok=True)
        nb_cm_path = os.path.join(MODELS_DIR, "nb_val_confusion_matrix.json")
        with open(nb_cm_path, "w") as f:
            json.dump(nb_metrics["confusion_matrix"], f)
        mlflow.log_artifact(nb_cm_path, artifact_path="validation")
        
    # -------------------------------------------------------------
    # RUN 2: Logistic Regression (Champion Candidate)
    # -------------------------------------------------------------
    logger.info("Training Model 2: Logistic Regression...")
    with mlflow.start_run(run_name="Candidate_LogisticRegression"):
        mlflow.log_param("model_family", "LogisticRegression")
        mlflow.log_param("C", lr_params.get("C", 2.0))
        mlflow.log_param("max_iter", lr_params.get("max_iter", 1000))
        mlflow.log_param("class_weight", lr_params.get("class_weight", "balanced"))
        mlflow.log_param("tfidf_max_features", tfidf_params.get("max_features", 25000))
        mlflow.log_param("tfidf_ngram_range", str(tfidf_ngram))
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("random_seed", ds_params.get("random_seed", 42))
        
        lr_pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                max_features=tfidf_params.get("max_features", 25000),
                ngram_range=tfidf_ngram,
                stop_words=tfidf_params.get("stop_words", "english"),
                sublinear_tf=tfidf_params.get("sublinear_tf", True)
            )),
            ("classifier", LogisticRegression(
                C=lr_params.get("C", 2.0),
                max_iter=lr_params.get("max_iter", 1000),
                class_weight=lr_params.get("class_weight", "balanced"),
                random_state=ds_params.get("random_seed", 42)
            ))
        ])
        
        lr_pipeline.fit(X_train, y_train)
        lr_metrics = evaluate_pipeline(lr_pipeline, X_val, y_val)
        
        mlflow.log_metric("val_accuracy", lr_metrics["accuracy"])
        mlflow.log_metric("val_precision", lr_metrics["precision"])
        mlflow.log_metric("val_recall", lr_metrics["recall"])
        mlflow.log_metric("val_f1_score", lr_metrics["f1_score"])
        mlflow.log_metric("val_false_positives", lr_metrics["false_positives"])
        mlflow.log_metric("val_false_negatives", lr_metrics["false_negatives"])
        
        lr_cm_path = os.path.join(MODELS_DIR, "lr_val_confusion_matrix.json")
        with open(lr_cm_path, "w") as f:
            json.dump(lr_metrics["confusion_matrix"], f)
        mlflow.log_artifact(lr_cm_path, artifact_path="validation")
        
    # -------------------------------------------------------------
    # MODEL SELECTION & COMPARISON
    # -------------------------------------------------------------
    # Prioritize F1 and lower false positives
    if nb_metrics["false_positives"] < lr_metrics["false_positives"] and nb_metrics["f1_score"] >= (lr_metrics["f1_score"] - 1.0):
        champion_name = "Multinomial Naive Bayes"
        champion_pipeline = nb_pipeline
        champion_metrics = nb_metrics
    else:
        champion_name = "Logistic Regression"
        champion_pipeline = lr_pipeline
        champion_metrics = lr_metrics
        
    logger.info(f"Model Selection Result: Selected {champion_name}")
    logger.info(f"  • MNB Validation: F1={nb_metrics['f1_score']}%, FP={nb_metrics['false_positives']}")
    logger.info(f"  • LR  Validation: F1={lr_metrics['f1_score']}%, FP={lr_metrics['false_positives']}")
    
    # Save Candidate Pipeline for Quality Gate evaluation
    candidate_path = os.path.join(MODELS_DIR, "candidate_pipeline.joblib")
    joblib.dump(champion_pipeline, candidate_path)
    logger.info(f"Saved candidate champion pipeline to {candidate_path}")
    
    metadata = {
        "selected_model": champion_name,
        "version": "v3.8.2",
        "random_seed": ds_params.get("random_seed", 42),
        "validation_metrics": champion_metrics,
        "comparison": {
            "naive_bayes": {
                "f1_score": nb_metrics["f1_score"],
                "precision": nb_metrics["precision"],
                "recall": nb_metrics["recall"],
                "false_positives": nb_metrics["false_positives"]
            },
            "logistic_regression": {
                "f1_score": lr_metrics["f1_score"],
                "precision": lr_metrics["precision"],
                "recall": lr_metrics["recall"],
                "false_positives": lr_metrics["false_positives"]
            }
        },
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    meta_path = os.path.join(MODELS_DIR, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Saved model metadata to {meta_path}")

if __name__ == "__main__":
    train_and_track()

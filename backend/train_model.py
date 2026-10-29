import os
import time
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

def train_and_export_model():
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../enron_spam_data.csv"))
    if not os.path.exists(data_path):
        data_path = "D:/MLOps/enron_spam_data.csv"
        
    print(f"Loading dataset from: {data_path}")
    start_time = time.time()
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows in {time.time() - start_time:.2f}s")
    
    # Merge Subject and Message
    df["Subject"] = df["Subject"].fillna("")
    df["Message"] = df["Message"].fillna("")
    df["text"] = df["Subject"] + " " + df["Message"]
    
    # Map label: spam -> 1, ham -> 0
    df = df.dropna(subset=["Spam/Ham"])
    df["label"] = df["Spam/Ham"].map(lambda x: 1 if str(x).strip().lower() == "spam" else 0)
    
    # Stratified Train/Test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )
    
    print(f"Training set: {len(X_train)}, Test set: {len(X_test)}")
    print("Building TF-IDF + LogisticRegression pipeline...")
    
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=25000,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True
        )),
        ("classifier", LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])
    
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print("=== MODEL EVALUATION METRICS ===")
    print(f"Accuracy : {acc * 100:.2f}%")
    print(f"Precision: {prec * 100:.2f}%")
    print(f"Recall   : {rec * 100:.2f}%")
    print(f"F1-Score : {f1 * 100:.2f}%")
    print(classification_report(y_test, y_pred, target_names=["Ham", "Spam"]))
    
    save_dir = os.path.join(os.path.dirname(__file__), "saved_models")
    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(save_dir, "spam_classifier.joblib")
    
    payload = {
        "pipeline": pipeline,
        "version": "v3.8.2",
        "metrics": {
            "accuracy": round(float(acc) * 100, 2),
            "precision": round(float(prec) * 100, 2),
            "recall": round(float(rec) * 100, 2),
            "f1": round(float(f1) * 100, 2),
            "test_samples": len(y_test)
        },
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    joblib.dump(payload, model_path)
    print(f"Model saved successfully to {model_path}!")

if __name__ == "__main__":
    train_and_export_model()


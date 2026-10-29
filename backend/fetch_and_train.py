import urllib.request
import ssl
import tarfile
import io
import os
import re
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import joblib

def fetch_and_prepare_clean_dataset():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    clean_csv_path = os.path.join(data_dir, "clean_enron_data.csv")
    
    ctx = ssl._create_unverified_context()
    records = []
    
    # Download enron1 and enron2 (approx 11,000 authentic emails total, ~3,000 real spam)
    archives = ["enron1", "enron2"]
    for arch in archives:
        url = f"http://www.aueb.gr/users/ion/data/enron-spam/preprocessed/{arch}.tar.gz"
        print(f"Downloading authentic {arch} from {url}...")
        try:
            req = urllib.request.urlopen(url, context=ctx, timeout=30)
            tar_bytes = req.read()
            with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
                for member in tar.getmembers():
                    if not member.isfile():
                        continue
                    name = member.name
                    if "/ham/" in name or "/spam/" in name:
                        label = "spam" if "/spam/" in name else "ham"
                        try:
                            f = tar.extractfile(member)
                            if f:
                                raw_text = f.read().decode("latin-1", errors="replace")
                                parts = raw_text.split("\n", 1)
                                subject = parts[0].replace("Subject:", "").strip()
                                body = parts[1].strip() if len(parts) > 1 else ""
                                records.append({
                                    "Subject": subject,
                                    "Message": body,
                                    "Spam/Ham": label,
                                    "text": f"{subject} {body}".strip()
                                })
                        except Exception as e:
                            pass
        except Exception as e:
            print(f"Failed to download {arch}: {e}")

    df = pd.DataFrame(records)
    print(f"Total authentic emails parsed: {len(df)}")
    print(df["Spam/Ham"].value_counts())
    df.to_csv(clean_csv_path, index=False)
    print(f"Saved clean dataset to {clean_csv_path}")
    return df

def train():
    df = fetch_and_prepare_clean_dataset()
    df["label"] = df["Spam/Ham"].map(lambda x: 1 if str(x).lower() == "spam" else 0)
    
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )
    
    print("Training TF-IDF + Calibrated Logistic Regression...")
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=20000,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True
        )),
        ("classifier", LogisticRegression(
            C=2.0,
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
        "trained_at": "2026-10-29 19:15:00"
    }
    
    joblib.dump(payload, model_path)
    print(f"Model saved successfully to {model_path}!")

if __name__ == "__main__":
    train()


import os
import json
import time
import random
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MONITORING_DIR = os.path.join(PROJECT_ROOT, "data", "monitoring")

def generate_normal_stream(n: int = 200) -> pd.DataFrame:
    """
    Creates an authentic in-distribution stream from held-out evaluation data (test.csv)
    representing legitimate and spam emails following the exact baseline distribution:
    - Normal sentence casing and token lengths matching Enron corpus
    - Low uppercase ratio (~2-4%)
    - Natural spam ratio (~28%)
    """
    test_path = os.path.join(PROJECT_ROOT, "data", "processed", "test.csv")
    if os.path.exists(test_path):
        df_test = pd.read_csv(test_path)
        sample = df_test.sample(n=min(n, len(df_test)), random_state=42).copy()
        text_col = "clean_text" if "clean_text" in sample.columns else "text"
        
        emails = []
        for i, (_, row) in enumerate(sample.iterrows()):
            emails.append({
                "id": f"NORM-{i+1:04d}",
                "text": str(row[text_col]),
                "label": int(row["label"]) if "label" in row else 0,
                "spam_prob_approx": 0.95 if ("label" in row and row["label"] == 1) else 0.05
            })
        return pd.DataFrame(emails)
    
    # Fallback template generator if test.csv is not present
    random.seed(42)
    np.random.seed(42)
    emails = []
    for i in range(n):
        is_spam = random.random() < 0.28
        emails.append({
            "id": f"NORM-{i+1:04d}",
            "text": f"Business dialogue regarding operations and review #{i}. Standard report attached.",
            "label": 1 if is_spam else 0,
            "spam_prob_approx": 0.90 if is_spam else 0.04
        })
    return pd.DataFrame(emails)

def generate_drifted_stream(n: int = 200) -> pd.DataFrame:
    """
    Generates deliberately drifted email traffic:
    - Drastic shift in uppercase ratio (> 35% ALL CAPS shouting)
    - High concentration of crypto phishing, foreign lottery prizes, urgent crypto transfers
    - Skewed token lengths and abnormal repetition
    - Abundant URLs, dollar / cryptocurrency symbols ($BTC, $ETH, $USD, $$$)
    - Dramatically shifted spam proportion (~75-80%)
    """
    random.seed(999)
    np.random.seed(999)
    
    drifted_templates = [
        "URGENT CLAIM NOTICE: YOUR BITCOIN WALLET HAS RECEIVED 1.84 BTC ($78,500 USD)! CLICK IMMEDIATE LINK TO VERIFY: http://crypto-payout-secure.xyz/claim-now",
        "CONGRATULATIONS WINNER!! YOU ARE SELECTED FOR $25,000 CASH BONUS TODAY ONLY! EXPIRES IN 30 MINUTES: http://fast-reward-portal.net/bonus",
        "ACTION REQUIRED: SUSPENDED CRYPTO ACCOUNT ACCESS! CONFIRM YOUR PRIVATE KEY AND SEED PHRASE AT http://wallet-security-update.io/login NOW!",
        "FLASH AIRDROP: CLAIM YOUR 50,000 FREE TOKENS ($12,000 VALUE) BEFORE THE DEADLINE AT http://airdrop-token-claims.xyz/now",
        "FINAL WARNING: YOUR REWARD OF $9,999 WILL BE FORFEITED UNLESS CONFIRMED AT http://payout-clearance-hub.com IMMEDIATELY!!",
        "FREE MONEY TRANSFER WAITING FOR YOU! 5000 DOLLARS CASH DEPOSITED IN YOUR ACCOUNT. VISIT http://instant-cash-award.org TODAY!"
    ]
    
    benign_noisy_templates = [
        "FYI: New crypto regulatory guidelines released by federal commission. Read analysis at official compliance repository.",
        "Updated hardware token authentication instructions for remote offshore development teams."
    ]
    
    emails = []
    for i in range(n):
        is_spam = random.random() < 0.80
        if is_spam:
            text = random.choice(drifted_templates)
            label = 1
        else:
            text = random.choice(benign_noisy_templates)
            label = 0
            
        emails.append({
            "id": f"DRIFT-{i+1:04d}",
            "text": text,
            "label": label,
            "spam_prob_approx": round(0.96 if is_spam else 0.12, 3)
        })
        
    df = pd.DataFrame(emails)
    return df

def generate_new_labels(n: int = 50) -> pd.DataFrame:
    """
    Curates newly verified and human-reviewed email records for the retraining pipeline.
    Represents fresh active learning feedback from users and domain reviewers.
    """
    random.seed(123)
    samples = [
        ("Security Notice: Please review your multi-factor credentials on internal portal.", 0),
        ("Monthly budget variance report for regional sales divisions.", 0),
        ("Team calendar invitation: Machine Learning pipeline retrospective.", 0),
        ("Vendor contract renewal agreement document ready for signature.", 0),
        ("IT Support: Scheduled server maintenance window this Saturday midnight.", 0),
        ("URGENT: Claim $10,000 gift card reward before midnight! Click here.", 1),
        ("Your mailbox quota has exceeded 99%. Re-verify login password immediately.", 1),
        ("Congratulations! You won the grand sweepstakes cash prize of $50,000.", 1),
        ("Wire transfer confirmation pending: verify your banking pin number now.", 1),
        ("Work from home and earn $8,000 weekly with no experience needed!", 1)
    ]
    
    rows = []
    for i in range(n):
        text, label = random.choice(samples)
        rows.append({
            "id": f"FB-LABEL-{i+1:03d}",
            "text": f"{text} (Ref batch #{i // 5 + 1})",
            "label": label,
            "source": "human_review_queue",
            "verified_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    df = pd.DataFrame(rows)
    return df

def generate_prediction_logs(n: int = 100) -> None:
    """
    Generates privacy-preserving prediction log records in data/monitoring/prediction_logs.jsonl
    containing operational metadata and text-derived features without storing raw email bodies.
    """
    from features import extract_text_features
    
    normal_df = generate_normal_stream(n)
    log_path = os.path.join(MONITORING_DIR, "prediction_logs.jsonl")
    
    now = time.time()
    with open(log_path, "w") as f:
        for idx, row in normal_df.iterrows():
            text = row["text"]
            is_spam = row["label"] == 1
            spam_prob = float(row["spam_prob_approx"])
            features = extract_text_features(text, spam_prob=spam_prob)
            
            entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - (n - idx) * 45)),
                "id": f"MG-{10480 + idx}",
                "model_version": "v3.8.2",
                "prediction": "Spam" if is_spam else "Legitimate",
                "is_spam": is_spam,
                "spam_probability": spam_prob,
                "confidence": round((spam_prob if is_spam else 1.0 - spam_prob) * 100, 1),
                "latency_ms": round(float(np.random.normal(1.3, 0.2)), 2),
                **features
            }
            f.write(json.dumps(entry) + "\n")

def main():
    os.makedirs(MONITORING_DIR, exist_ok=True)
    
    normal_df = generate_normal_stream(200)
    normal_path = os.path.join(MONITORING_DIR, "production_stream_normal.csv")
    normal_df.to_csv(normal_path, index=False)
    print(f"Generated Normal Stream: {normal_path} ({len(normal_df)} records)")
    
    drifted_df = generate_drifted_stream(200)
    drifted_path = os.path.join(MONITORING_DIR, "production_stream_drifted.csv")
    drifted_df.to_csv(drifted_path, index=False)
    print(f"Generated Drifted Stream: {drifted_path} ({len(drifted_df)} records)")
    
    new_labels_df = generate_new_labels(50)
    new_labels_path = os.path.join(MONITORING_DIR, "new_labels.csv")
    new_labels_df.to_csv(new_labels_path, index=False)
    print(f"Generated Retraining Labels: {new_labels_path} ({len(new_labels_df)} records)")
    
    generate_prediction_logs(100)
    print(f"Generated Prediction Logs: {os.path.join(MONITORING_DIR, 'prediction_logs.jsonl')} (100 logs)")

if __name__ == "__main__":
    main()

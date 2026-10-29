import os
import re
import yaml
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preprocess")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PARAMS_FILE = os.path.join(PROJECT_ROOT, "params.yaml")

def load_params():
    if os.path.exists(PARAMS_FILE):
        with open(PARAMS_FILE, "r") as f:
            return yaml.safe_load(f)
    return {}

def clean_text(text: str) -> str:
    """
    Standardizes email text:
    - Normalizes case to lowercase
    - Normalizes URLs, email addresses, and currency symbols
    - Removes excessive punctuation, control characters, and redundant whitespace
    """
    if not isinstance(text, str):
        return ""
    
    t = text.lower()
    
    # Replace URLs
    t = re.sub(r'https?://\S+|www\.\S+', ' [url] ', t)
    
    # Replace Email addresses
    t = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' [email] ', t)
    
    # Replace currency amounts
    t = re.sub(r'[\$£€]\s*\d+([.,]\d+)?|\b\d+([.,]\d+)?\s*(dollars|usd|euros)\b', ' [money] ', t)
    
    # Replace multiple spaces, newlines, and tabs
    t = re.sub(r'\s+', ' ', t).strip()
    
    return t

def preprocess_and_split():
    params = load_params()
    ds_params = params.get("dataset", {})
    
    raw_path = os.path.join(PROJECT_ROOT, ds_params.get("raw_path", "data/raw/enron_spam_data.csv"))
    output_dir = os.path.join(PROJECT_ROOT, ds_params.get("processed_dir", "data/processed"))
    random_seed = ds_params.get("random_seed", 42)
    test_size = ds_params.get("test_size", 0.15)
    val_size = ds_params.get("val_size", 0.15)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # If raw dataset is not present, use ingestion script
    if not os.path.exists(raw_path):
        from ingestion import load_data
        df = load_data()
    else:
        logger.info(f"Loading raw dataset from {raw_path}...")
        df = pd.read_csv(raw_path)
        
    initial_count = len(df)
    
    # Normalize column names
    col_map = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=col_map)
    if "spam/ham" in df.columns:
        df["label"] = df["spam/ham"].map(lambda x: 1 if str(x).lower() == "spam" else 0)
    elif "raw_label" in df.columns:
        df["label"] = df["raw_label"].map(lambda x: 1 if str(x).lower() == "spam" else 0)
        
    df["subject"] = df["subject"].fillna("") if "subject" in df.columns else ""
    df["message"] = df["message"].fillna("") if "message" in df.columns else ""
    
    # Combine subject and message
    df["text"] = df.apply(lambda r: f"{r['subject']} {r['message']}".strip(), axis=1)
    
    logger.info("Cleaning and normalizing text content...")
    df["clean_text"] = df["text"].apply(clean_text)
    
    # Filter empty texts
    df = df[df["clean_text"].str.strip() != ""].copy()
    
    # Deduplicate
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["clean_text"]).copy()
    logger.info(f"Deduplicated dataset: {before_dedup - len(df)} duplicate emails removed. Remaining: {len(df)}")
    
    # Stratified Train / Temp Split
    temp_ratio = test_size + val_size
    train_df, temp_df = train_test_split(
        df,
        test_size=temp_ratio,
        random_state=random_seed,
        stratify=df["label"]
    )
    
    # Split Temp into Val and Test
    val_ratio_in_temp = val_size / temp_ratio
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1.0 - val_ratio_in_temp),
        random_state=random_seed,
        stratify=temp_df["label"]
    )
    
    logger.info(f"Splits -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    train_path = os.path.join(output_dir, "train.csv")
    val_path = os.path.join(output_dir, "val.csv")
    test_path = os.path.join(output_dir, "test.csv")
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Processed splits saved to {output_dir}")
    return train_df, val_df, test_df

if __name__ == "__main__":
    preprocess_and_split()

import re
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

URL_REGEX = re.compile(r'https?://\S+|www\.\S+|\b[A-Za-z0-9.-]+\.(?:com|org|net|edu|gov|io|xyz|info|biz)\b', re.IGNORECASE)
CURRENCY_REGEX = re.compile(r'[\$£€¥₹]\s*\d+|\b\d+\s*(?:dollars?|usd|euros?|pounds?|cash|bucks)\b|\b(?:lottery|prize|reward|winner|claim)\b', re.IGNORECASE)
UPPERCASE_REGEX = re.compile(r'[A-Z]')
DIGIT_REGEX = re.compile(r'\d')

def extract_text_features(text: str, spam_prob: Optional[float] = None) -> Dict[str, Any]:
    """
    Extracts privacy-preserving, text-derived numerical features from email text.
    No raw email body or personally identifiable information is stored.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            "char_length": 0,
            "token_count": 0,
            "uppercase_ratio": 0.0,
            "digit_count": 0,
            "url_count": 0,
            "currency_count": 0,
            "spam_probability": float(spam_prob) if spam_prob is not None else 0.0
        }

    raw_len = len(text)
    tokens = text.split()
    token_count = len(tokens)
    
    # Uppercase character proportion
    uppercase_count = len(UPPERCASE_REGEX.findall(text))
    uppercase_ratio = round(uppercase_count / max(1, raw_len), 4)
    
    # Digit and symbol indicators
    digit_count = len(DIGIT_REGEX.findall(text))
    url_count = len(URL_REGEX.findall(text))
    currency_count = len(CURRENCY_REGEX.findall(text))
    
    return {
        "char_length": raw_len,
        "token_count": token_count,
        "uppercase_ratio": uppercase_ratio,
        "digit_count": digit_count,
        "url_count": url_count,
        "currency_count": currency_count,
        "spam_probability": round(float(spam_prob), 4) if spam_prob is not None else 0.0
    }

def extract_features_dataframe(df: pd.DataFrame, text_column: str = "text", model_pipeline=None) -> pd.DataFrame:
    """
    Transforms a DataFrame with email text into a DataFrame of numerical features
    for drift monitoring and distribution analysis.
    """
    if text_column not in df.columns:
        # Fallback to 'message' or 'clean_text' if 'text' isn't directly present
        if "clean_text" in df.columns:
            text_column = "clean_text"
        elif "message" in df.columns:
            text_column = "message"
        else:
            raise KeyError(f"None of ['{text_column}', 'clean_text', 'message'] found in DataFrame columns: {df.columns.tolist()}")

    texts = df[text_column].fillna("").astype(str).tolist()
    
    # Predict spam probabilities if model pipeline is supplied
    probabilities = None
    if model_pipeline is not None and hasattr(model_pipeline, "predict_proba"):
        try:
            prob_arr = model_pipeline.predict_proba(texts)
            probabilities = prob_arr[:, 1]
        except Exception:
            probabilities = None

    rows = []
    for i, t in enumerate(texts):
        prob = probabilities[i] if probabilities is not None else (
            float(df["spam_probability"].iloc[i]) if "spam_probability" in df.columns else (
                1.0 if "label" in df.columns and df["label"].iloc[i] == 1 else 0.0
            )
        )
        rows.append(extract_text_features(t, spam_prob=prob))

    feature_df = pd.DataFrame(rows)
    return feature_df


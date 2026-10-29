import os
import io
import ssl
import tarfile
import urllib.request
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingestion")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
OUTPUT_RAW_CSV = os.path.join(DATA_RAW_DIR, "enron_spam_data.csv")
CLEAN_ENRON_CSV = os.path.join(PROJECT_ROOT, "backend", "data", "clean_enron_data.csv")
PARENT_CSV = "D:/MLOps/enron_spam_data.csv"

def download_and_extract_enron_corpus():
    """
    Downloads and extracts all authentic Enron-Spam archives from the original
    Athens University of Economics and Business benchmark repository with proper User-Agent headers.
    """
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    ctx = ssl._create_unverified_context()
    records = []
    
    logger.info("Fetching authentic Enron-Spam archives...")
    for i in range(1, 7):
        arch_name = f"enron{i}"
        url = f"http://www.aueb.gr/users/ion/data/enron-spam/preprocessed/{arch_name}.tar.gz"
        logger.info(f"Downloading {arch_name} from {url}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
                tar_bytes = response.read()
                with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
                    for member in tar.getmembers():
                        if not member.isfile():
                            continue
                        name = member.name
                        if "/ham/" in name or "/spam/" in name:
                            label_str = "spam" if "/spam/" in name else "ham"
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
                                        "Spam/Ham": label_str
                                    })
                            except Exception as e:
                                pass
        except Exception as e:
            logger.warning(f"Error fetching {arch_name}: {e}")

    if not records:
        raise RuntimeError("No records could be extracted from Enron archives.")
        
    df = pd.DataFrame(records)
    logger.info(f"Assembled {len(df)} authentic email records.")
    df.to_csv(OUTPUT_RAW_CSV, index=False)
    logger.info(f"Saved authentic Enron dataset to {OUTPUT_RAW_CSV}")
    return df

def validate_and_standardize_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates column presence, strips whitespace, standardizes column names,
    and maps class labels to binary integers (1: spam, 0: ham).
    """
    col_map = {}
    for col in df.columns:
        norm = col.strip().lower()
        if norm in ["subject", "sub"]:
            col_map[col] = "subject"
        elif norm in ["message", "body", "text", "content"]:
            col_map[col] = "message"
        elif norm in ["spam/ham", "label", "target", "class", "is_spam"]:
            col_map[col] = "raw_label"
            
    df = df.rename(columns=col_map)
    
    required_cols = ["subject", "message", "raw_label"]
    for req in required_cols:
        if req not in df.columns:
            if req == "subject":
                df["subject"] = ""
            elif req == "message":
                raise ValueError(f"Required column 'message' missing! Available: {df.columns.tolist()}")
            elif req == "raw_label":
                raise ValueError(f"Required column 'raw_label' (Spam/Ham) missing!")
                
    def map_label(val):
        s = str(val).strip().lower()
        if s in ["1", "spam", "true", "yes"]:
            return 1
        elif s in ["0", "ham", "legitimate", "false", "no"]:
            return 0
        return None

    df["label"] = df["raw_label"].map(map_label)
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    
    return df[["subject", "message", "raw_label", "label"]]

def load_data(force_refresh: bool = False) -> pd.DataFrame:
    """
    Loads dataset from raw cache, clean enron cache, or candidate sources.
    """
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    
    if not force_refresh and os.path.exists(OUTPUT_RAW_CSV):
        logger.info(f"Loading cached raw dataset from {OUTPUT_RAW_CSV}")
        df = pd.read_csv(OUTPUT_RAW_CSV)
    elif not force_refresh and os.path.exists(CLEAN_ENRON_CSV):
        logger.info(f"Loading verified authentic Enron dataset from {CLEAN_ENRON_CSV}...")
        df = pd.read_csv(CLEAN_ENRON_CSV)
        # Also copy to raw dir
        df.to_csv(OUTPUT_RAW_CSV, index=False)
    elif not force_refresh and os.path.exists(PARENT_CSV):
        logger.info(f"Inspecting candidate CSV at {PARENT_CSV}...")
        df_candidate = pd.read_csv(PARENT_CSV)
        spam_subset = df_candidate[df_candidate.get("Spam/Ham", "").str.lower() == "spam"]
        unique_spam = spam_subset["Message"].nunique() if "Message" in spam_subset else 0
        
        if unique_spam <= 10:
            logger.warning(
                f"Candidate dataset at {PARENT_CSV} has corrupted spam data (only {unique_spam} unique spam texts). "
                "Fetching authentic Enron corpus..."
            )
            df = download_and_extract_enron_corpus()
        else:
            df = df_candidate
    else:
        logger.info("Raw dataset not found locally. Downloading authentic Enron corpus...")
        df = download_and_extract_enron_corpus()
        
    df_clean = validate_and_standardize_schema(df)
    logger.info(f"Dataset successfully ingested. Total samples: {len(df_clean)}")
    logger.info(f"Distribution: Spam (1) = {(df_clean['label'] == 1).sum()}, Ham (0) = {(df_clean['label'] == 0).sum()}")
    return df_clean

if __name__ == "__main__":
    df = load_data()
    print("Ingestion complete. Shape:", df.shape)
    print(df.head())

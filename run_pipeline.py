import sys
import os
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.ingestion import load_data
from src.preprocess import preprocess_and_split
from src.train import train_and_select_model
from src.evaluate import run_evaluation

def main():
    start_time = time.time()
    print("=" * 65)
    print("      MAILGUARD MLOps PIPELINE: END-TO-END EXECUTION")
    print("=" * 65)
    
    # Step 1: Ingestion
    print("\n>>> STEP 1: DATA INGESTION & SCHEMA VALIDATION")
    df_raw = load_data()
    print(f"Ingested {len(df_raw)} records successfully.")
    
    # Step 2: Preprocessing & Splitting
    print("\n>>> STEP 2: DATA PREPROCESSING & STRATIFIED SPLIT")
    train_df, val_df, test_df = preprocess_and_split(df_raw)
    print(f"Splits created: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    # Step 3: Model Training & Model Selection
    print("\n>>> STEP 3: MODEL TRAINING & SELECTION (NB vs LR)")
    champion_pipeline, metadata = train_and_select_model()
    print(f"Champion model: {metadata['model_name']}")
    
    # Step 4: Held-out Test Set Evaluation
    print("\n>>> STEP 4: HELD-OUT TEST EVALUATION (ZERO LEAKAGE)")
    eval_results = run_evaluation()
    
    elapsed = time.time() - start_time
    print(f"\nPipeline finished in {elapsed:.2f} seconds.")
    print("Artifacts saved:")
    print("  • Model Pipeline   : models/spam_pipeline.joblib")
    print("  • Model Metadata   : models/model_metadata.json")
    print("  • Evaluation Report: models/evaluation_results.json")
    print("=" * 65)

if __name__ == "__main__":
    main()


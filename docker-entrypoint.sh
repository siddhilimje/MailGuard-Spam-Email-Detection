#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting MailGuard API Service (Container Initialization)"
echo "=========================================================="

# Ensure expected directories exist
mkdir -p /app/models /app/data/monitoring /app/reports/monitoring /app/mlruns

# Documented & reproducible model artifact resolution
MODEL_FILE="/app/models/spam_pipeline.joblib"
BACKUP_MODEL="/app/backend/saved_models/spam_classifier.joblib"

if [ ! -f "$MODEL_FILE" ]; then
    echo "[Entrypoint] Model artifact missing at $MODEL_FILE."
    if [ -f "$BACKUP_MODEL" ]; then
        echo "[Entrypoint] Restoring baseline model from backup package..."
        cp "$BACKUP_MODEL" "$MODEL_FILE"
    else
        echo "[Entrypoint] No existing model found. Running reproducible pipeline training..."
        python run_pipeline.py || python src/train.py
    fi
fi

if [ -f "$MODEL_FILE" ]; then
    echo "[Entrypoint] Model artifact verified at $MODEL_FILE"
else
    echo "[Entrypoint] FATAL: Failed to resolve model artifact!"
    exit 1
fi

echo "[Entrypoint] Launching application command: $@"
exec "$@"


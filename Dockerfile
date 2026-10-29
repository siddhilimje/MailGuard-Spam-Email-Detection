# ========================================================
# Stage 1: Builder — Dependencies Compilation
# ========================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install minimal build tools for wheels compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .

# Install dependencies into dedicated user directory
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ========================================================
# Stage 2: Production Runtime
# ========================================================
FROM python:3.11-slim AS runtime

# Set performance and security environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/app:${PYTHONPATH}" \
    MLFLOW_TRACKING_URI="file:///app/mlruns" \
    MLFLOW_ALLOW_FILE_STORE="true"

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group for container security
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1001 -m -s /bin/bash appuser

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code, pipeline source, parameters and model artifacts
COPY backend/ ./backend/
COPY src/ ./src/
COPY models/ ./models/
COPY data/monitoring/ ./data/monitoring/
COPY reports/ ./reports/
COPY params.yaml .
COPY docker-entrypoint.sh .

# Ensure entrypoint is executable and ownership belongs to non-root appuser
RUN chmod +x /app/docker-entrypoint.sh && \
    mkdir -p /app/mlruns /app/data/monitoring /app/reports/monitoring /app/models && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Docker Healthcheck to verify service and model readiness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]


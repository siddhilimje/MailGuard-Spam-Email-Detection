from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

class EmailPredictRequest(BaseModel):
    sender: Optional[str] = Field(default="sender@example.com", max_length=254)
    subject: Optional[str] = Field(default="", max_length=500)
    body: Optional[str] = Field(default="", max_length=50000)

    @field_validator("body", mode="after")
    @classmethod
    def validate_content_presence(cls, v, info):
        # We also need to check subject from values if available
        return v

    def validate_non_empty(self):
        sub = (self.subject or "").strip()
        msg = (self.body or "").strip()
        if not sub and not msg:
            raise ValueError("Email subject line and message body cannot both be empty.")

class BatchEmailPredictRequest(BaseModel):
    emails: List[EmailPredictRequest] = Field(min_length=1, max_length=100)

class RiskBreakdown(BaseModel):
    content_signals: int
    sender_reputation: int
    link_safety: int

class FlaggedReason(BaseModel):
    title: str
    severity: str
    description: str

class PredictionResponse(BaseModel):
    id: str
    label: str  # "spam" or "legitimate"
    is_spam: bool
    spam_probability: float  # raw model posterior probability
    confidence: float        # probability associated with the predicted class
    verdict_title: str
    recommendation: str
    risk_breakdown: RiskBreakdown
    flagged_reasons: List[FlaggedReason]
    model_version: str
    latency_ms: float
    timestamp: str
    subject_snippet: str

class BatchPredictionResponse(BaseModel):
    total: int
    spam_count: int
    legitimate_count: int
    batch_latency_ms: float
    predictions: List[PredictionResponse]

class FeedbackRequest(BaseModel):
    scan_id: Optional[str] = "MG-10482"
    subject: Optional[str] = ""
    user_verdict: str
    model_verdict: Optional[str] = "Spam"
    comments: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
    uptime_seconds: float
    services: Dict[str, str]

class ModelInfoResponse(BaseModel):
    model_name: str
    version: str
    artifact_path: str
    random_seed: int
    training_samples: int
    test_samples: int
    evaluation_metrics: Dict[str, Any]
    confusion_matrix: Dict[str, int]
    quality_gate_status: str
    trained_at: str

class OperationalMetricsResponse(BaseModel):
    total_predictions: int
    total_spam_detected: int
    total_legitimate_detected: int
    spam_ratio_percent: float
    avg_latency_ms: float
    p95_latency_ms: float
    error_count: int
    uptime_seconds: float


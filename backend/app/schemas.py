from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    database_connected: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DatasetGenerateRequest(BaseModel):
    n_customers: int = Field(default=350, ge=10, le=5000)
    seed: int = Field(default=42)
    corrupt: bool = Field(default=False)
    corruption_rate: float = Field(default=0.05, ge=0.0, le=0.5)


class ExecutiveSummaryResponse(BaseModel):
    period: Dict[str, Any]
    metrics: Dict[str, Any]


class ModelTrainRequest(BaseModel):
    model_type: str = Field(default="RandomForest", description="RandomForest, LogisticRegression, or Baseline")
    observation_days: int = Field(default=90, ge=30, le=365)
    prediction_days: int = Field(default=60, ge=14, le=180)
    target_recall: float = Field(default=0.75, ge=0.1, le=1.0)


class AssistantRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)


class CustomerFilterParams(BaseModel):
    search: Optional[str] = None
    segment: Optional[str] = None
    channel: Optional[str] = None
    page: int = 1
    page_size: int = 50

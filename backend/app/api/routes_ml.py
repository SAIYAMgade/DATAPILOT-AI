from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import ModelVersion
from backend.app.ml.models import ModelTrainingService
from backend.app.ml.prioritization import RetentionPrioritizationEngine
from backend.app.schemas import ModelTrainRequest

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/train")
def train_model(payload: ModelTrainRequest, db: Session = Depends(get_db)):
    service = ModelTrainingService(db)
    result = service.train_and_evaluate(
        model_type=payload.model_type,
        observation_days=payload.observation_days,
        prediction_days=payload.prediction_days,
        target_recall=payload.target_recall
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Auto-generate fresh customer priorities using new model
    p_engine = RetentionPrioritizationEngine(db)
    p_engine.generate_predictions_and_priorities()

    return result


@router.get("/versions")
def list_model_versions(db: Session = Depends(get_db)):
    models = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "version_tag": m.version_tag,
            "model_type": m.model_type,
            "observation_days": m.observation_days,
            "prediction_days": m.prediction_days,
            "threshold": m.threshold,
            "is_active": m.is_active,
            "metrics": m.metrics,
            "feature_importance": m.feature_importance,
            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for m in models
    ]


@router.get("/active")
def get_active_model(db: Session = Depends(get_db)):
    m = db.query(ModelVersion).filter_by(is_active=True).first()
    if not m:
        return {"active": False, "message": "No active model version available."}
    return {
        "active": True,
        "id": m.id,
        "version_tag": m.version_tag,
        "model_type": m.model_type,
        "observation_days": m.observation_days,
        "prediction_days": m.prediction_days,
        "threshold": m.threshold,
        "metrics": m.metrics,
        "feature_importance": m.feature_importance,
        "created_at": m.created_at.strftime("%Y-%m-%d %H:%M")
    }


@router.get("/predictions")
def get_prioritized_predictions(
    limit: int = Query(50, ge=5, le=500),
    db: Session = Depends(get_db)
):
    engine = RetentionPrioritizationEngine(db)
    result = engine.generate_predictions_and_priorities(limit=limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

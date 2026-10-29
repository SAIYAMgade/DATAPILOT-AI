from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import BusinessInsight
from backend.app.insights import BusinessInsightEngine

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("")
def list_insights(db: Session = Depends(get_db)):
    records = db.query(BusinessInsight).order_by(BusinessInsight.id.asc()).all()
    if not records:
        # Recompute on the fly if table is empty
        engine = BusinessInsightEngine(db)
        return engine.generate_all_insights()

    return [
        {
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "metric_name": r.metric_name,
            "comparison_period": r.comparison_period,
            "current_value": r.current_value,
            "previous_value": r.previous_value,
            "change_pct": r.change_pct,
            "severity": r.severity,
            "supporting_evidence": r.supporting_evidence,
            "limitations": r.limitations,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for r in records
    ]


@router.post("/refresh")
def refresh_insights(db: Session = Depends(get_db)):
    engine = BusinessInsightEngine(db)
    return engine.generate_all_insights()

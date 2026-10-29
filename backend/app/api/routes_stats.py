from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.analytics.statistics import StatisticalAnalysisEngine

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/segment-comparison")
def test_segment_comparison(
    group_col: str = Query("acquisition_channel", pattern="^(acquisition_channel|region)$"),
    db: Session = Depends(get_db)
):
    engine = StatisticalAnalysisEngine(db)
    return engine.test_segment_transaction_values(group_col=group_col)


@router.get("/channel-retention")
def test_channel_retention(db: Session = Depends(get_db)):
    engine = StatisticalAnalysisEngine(db)
    return engine.test_channel_retention_association()


@router.get("/confidence-intervals")
def get_confidence_intervals(
    confidence: float = Query(0.95, ge=0.80, le=0.99),
    db: Session = Depends(get_db)
):
    engine = StatisticalAnalysisEngine(db)
    return engine.compute_metric_confidence_intervals(confidence=confidence)


@router.get("/revenue-trend")
def test_revenue_trend(db: Session = Depends(get_db)):
    engine = StatisticalAnalysisEngine(db)
    return engine.test_monthly_revenue_trend()

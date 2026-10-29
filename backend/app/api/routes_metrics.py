from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.analytics.metrics import BusinessMetricsEngine

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary")
def get_executive_summary(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    engine = BusinessMetricsEngine(db)
    s_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    e_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    return engine.get_executive_summary(start_date=s_dt, end_date=e_dt)


@router.get("/time-series")
def get_revenue_time_series(
    granularity: str = Query("monthly", pattern="^(monthly|weekly)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    engine = BusinessMetricsEngine(db)
    s_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    e_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    return engine.get_revenue_time_series(granularity=granularity, start_date=s_dt, end_date=e_dt)


@router.get("/breakdowns")
def get_breakdowns(db: Session = Depends(get_db)):
    engine = BusinessMetricsEngine(db)
    return engine.get_breakdowns()


@router.get("/pareto")
def get_pareto_concentration(db: Session = Depends(get_db)):
    engine = BusinessMetricsEngine(db)
    return engine.get_pareto_concentration()

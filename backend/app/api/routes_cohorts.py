from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.analytics.cohorts import CohortRetentionEngine

router = APIRouter(prefix="/cohorts", tags=["Cohorts"])


@router.get("/matrix")
def get_cohort_matrix(db: Session = Depends(get_db)):
    engine = CohortRetentionEngine(db)
    return engine.compute_cohort_matrix()

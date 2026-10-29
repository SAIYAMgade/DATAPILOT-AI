from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.analytics.segmentation import CustomerSegmentationEngine

router = APIRouter(prefix="/segmentation", tags=["Segmentation"])


@router.get("/rfm")
def get_rfm_segmentation(db: Session = Depends(get_db)):
    engine = CustomerSegmentationEngine(db)
    return engine.compute_rfm_segments()

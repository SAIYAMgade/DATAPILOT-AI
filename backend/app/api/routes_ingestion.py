from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import DatasetBatch, IngestionRejection
from backend.app.generator import SyntheticDataGenerator
from backend.app.ingestion import IngestionEngine
from backend.app.schemas import DatasetGenerateRequest

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion & Quality"])


@router.post("/generate-and-seed")
def generate_and_seed_dataset(
    payload: DatasetGenerateRequest,
    db: Session = Depends(get_db)
):
    gen = SyntheticDataGenerator(seed=payload.seed)
    data_payload = gen.generate(
        n_customers=payload.n_customers,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2026, 4, 1),
        corrupt=payload.corrupt,
        corruption_rate=payload.corruption_rate
    )
    engine = IngestionEngine(db)
    result = engine.ingest_payload(data_payload, source_type="synthetic_api")
    return result


@router.get("/batches")
def list_batches(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    batches = db.query(DatasetBatch).order_by(DatasetBatch.id.desc()).limit(limit).all()
    return [
        {
            "id": b.id,
            "batch_ref": b.batch_ref,
            "source_type": b.source_type,
            "records_received": b.records_received,
            "records_accepted": b.records_accepted,
            "records_rejected": b.records_rejected,
            "status": b.status,
            "rejection_summary": b.rejection_summary,
            "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for b in batches
    ]


@router.get("/batches/{batch_id}/rejections")
def get_batch_rejections(
    batch_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    batch = db.query(DatasetBatch).filter_by(id=batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    rejections = db.query(IngestionRejection).filter_by(batch_id=batch_id).limit(limit).all()
    return {
        "batch_ref": batch.batch_ref,
        "total_rejected": batch.records_rejected,
        "sample": [
            {
                "row_index": r.row_index,
                "reason": r.reason,
                "raw_record": r.raw_record,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in rejections
        ]
    }

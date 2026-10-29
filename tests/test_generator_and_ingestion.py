import pytest
from datetime import datetime
from backend.app.generator import SyntheticDataGenerator
from backend.app.ingestion import IngestionEngine
from backend.app.models import DatasetBatch, IngestionRejection, Transaction


def test_generator_reproducibility():
    gen1 = SyntheticDataGenerator(seed=123)
    data1 = gen1.generate(n_customers=20, start_date=datetime(2025, 1, 1), end_date=datetime(2025, 6, 1))

    gen2 = SyntheticDataGenerator(seed=123)
    data2 = gen2.generate(n_customers=20, start_date=datetime(2025, 1, 1), end_date=datetime(2025, 6, 1))

    assert len(data1["customers"]) == len(data2["customers"])
    assert len(data1["transactions"]) == len(data2["transactions"])
    assert data1["customers"][0]["customer_ref"] == data2["customers"][0]["customer_ref"]
    assert data1["transactions"][0]["amount"] == data2["transactions"][0]["amount"]


def test_clean_ingestion(db_session):
    gen = SyntheticDataGenerator(seed=99)
    payload = gen.generate(n_customers=25, start_date=datetime(2025, 1, 1), end_date=datetime(2025, 4, 1))

    engine = IngestionEngine(db_session)
    result = engine.ingest_payload(payload, source_type="synthetic_test")

    assert result["status"] == "completed"
    assert result["records_rejected"] == 0
    assert result["records_accepted"] == len(payload["transactions"])

    batch = db_session.query(DatasetBatch).filter_by(batch_ref=result["batch_ref"]).first()
    assert batch is not None
    assert batch.records_accepted == result["records_accepted"]


def test_corrupted_ingestion_and_rejections(db_session):
    gen = SyntheticDataGenerator(seed=77)
    payload = gen.generate(
        n_customers=30,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 4, 1),
        corrupt=True,
        corruption_rate=0.20
    )

    engine = IngestionEngine(db_session)
    result = engine.ingest_payload(payload, source_type="corrupted_test")

    assert result["records_rejected"] > 0
    assert result["status"] in ["partial", "completed"]

    rejections = db_session.query(IngestionRejection).all()
    assert len(rejections) == result["records_rejected"]
    reasons = [r.reason for r in rejections]
    assert any("Duplicate" in r or "Invalid" in r or "Unresolved" in r for r in reasons)

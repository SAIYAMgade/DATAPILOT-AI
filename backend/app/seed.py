from datetime import datetime
from backend.app.database import SessionLocal
from backend.app.generator import SyntheticDataGenerator
from backend.app.ingestion import IngestionEngine


def run_seed():
    db = SessionLocal()
    try:
        print("Starting synthetic data generation...")
        gen = SyntheticDataGenerator(seed=42)
        payload = gen.generate(
            n_customers=350,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2026, 4, 1),
            corrupt=False
        )
        print(f"Generated {len(payload['customers'])} customers, {len(payload['transactions'])} transactions.")

        engine = IngestionEngine(db)
        result = engine.ingest_payload(payload, source_type="synthetic")
        print("Ingestion result:", result)
        return result
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

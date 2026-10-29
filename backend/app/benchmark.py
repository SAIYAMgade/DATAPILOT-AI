import time
import platform
import psutil
from datetime import datetime
from backend.app.database import SessionLocal
from backend.app.generator import SyntheticDataGenerator
from backend.app.ingestion import IngestionEngine
from backend.app.analytics.metrics import BusinessMetricsEngine
from backend.app.ml.features import FeatureEngineeringService
from backend.app.ml.models import ModelTrainingService
from backend.app.ml.prioritization import RetentionPrioritizationEngine


def run_benchmarks():
    print("=" * 60)
    print("DATAPILOT AI - REPRODUCIBLE SYSTEM BENCHMARK")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"OS: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {platform.python_version()}")
    print(f"CPU Count: {psutil.cpu_count(logical=True)}")
    print(f"Total RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB")
    print("-" * 60)

    db = SessionLocal()
    results = {}

    try:
        # 1. Dataset Generation Benchmark
        t0 = time.perf_counter()
        gen = SyntheticDataGenerator(seed=42)
        payload = gen.generate(n_customers=500, start_date=datetime(2025, 1, 1), end_date=datetime(2026, 4, 1))
        t_gen = time.perf_counter() - t0
        results["data_generation_time_s"] = round(t_gen, 4)
        print(f"1. Generation ({len(payload['customers'])} custs, {len(payload['transactions'])} txs): {t_gen:.3f}s")

        # 2. Ingestion & Validation Benchmark
        engine = IngestionEngine(db)
        t0 = time.perf_counter()
        ingest_res = engine.ingest_payload(payload, source_type="benchmark")
        t_ingest = time.perf_counter() - t0
        results["ingestion_time_s"] = round(t_ingest, 4)
        results["ingested_tx_per_second"] = round(ingest_res["records_accepted"] / max(0.001, t_ingest), 1)
        print(f"2. Ingestion & Validation ({ingest_res['records_accepted']} records): {t_ingest:.3f}s ({results['ingested_tx_per_second']} tx/sec)")

        # 3. SQL Analytics Queries Benchmark
        metrics_eng = BusinessMetricsEngine(db)
        t0 = time.perf_counter()
        _ = metrics_eng.get_executive_summary()
        _ = metrics_eng.get_revenue_time_series()
        _ = metrics_eng.get_breakdowns()
        _ = metrics_eng.get_pareto_concentration()
        t_analytics = time.perf_counter() - t0
        results["sql_analytics_time_s"] = round(t_analytics, 4)
        print(f"3. Complex SQL Analytical Queries (CTEs & Windows): {t_analytics:.3f}s")

        # 4. Feature Engineering Benchmark
        feat_service = FeatureEngineeringService(db)
        t0 = time.perf_counter()
        X, y = feat_service.extract_features_and_target(cutoff_date=datetime(2026, 1, 1), observation_days=90, prediction_days=60)
        t_features = time.perf_counter() - t0
        results["feature_engineering_time_s"] = round(t_features, 4)
        print(f"4. Temporal Feature Engineering ({len(X)} accounts): {t_features:.3f}s")

        # 5. Model Training Benchmark
        train_service = ModelTrainingService(db)
        t0 = time.perf_counter()
        train_res = train_service.train_and_evaluate(model_type="RandomForest")
        t_train = time.perf_counter() - t0
        results["model_training_time_s"] = round(t_train, 4)
        print(f"5. Random Forest Training & Threshold Tuning: {t_train:.3f}s (ROC-AUC: {train_res['metrics']['roc_auc']})")

        # 6. Prediction Latency Benchmark
        p_engine = RetentionPrioritizationEngine(db)
        t0 = time.perf_counter()
        p_res = p_engine.generate_predictions_and_priorities(limit=100)
        t_pred = time.perf_counter() - t0
        results["batch_prediction_latency_s"] = round(t_pred, 4)
        results["inference_latency_per_cust_ms"] = round((t_pred / max(1, p_res.get('total_customers_scored', 1))) * 1000, 3)
        print(f"6. Batch Inference & Priority Ranking: {t_pred:.3f}s ({results['inference_latency_per_cust_ms']} ms/customer)")

        # Memory usage
        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        results["process_memory_mb"] = round(mem_mb, 2)
        print(f"7. Resident Process Memory: {mem_mb:.2f} MB")
        print("=" * 60)
        print("BENCHMARK COMPLETED SUCCESSFULLY")
        print("=" * 60)

        return results
    finally:
        db.close()


if __name__ == "__main__":
    run_benchmarks()

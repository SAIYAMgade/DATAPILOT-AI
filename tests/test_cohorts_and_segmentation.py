import pytest
from datetime import datetime
from backend.app.analytics.cohorts import CohortRetentionEngine
from backend.app.analytics.segmentation import CustomerSegmentationEngine


def test_cohort_assignment_and_retention(db_session, seed_controlled_data):
    cohort_engine = CohortRetentionEngine(db_session)
    res = cohort_engine.compute_cohort_matrix()

    ret_matrix = res["retention_matrix"]
    # All 3 controlled customers signed up and had transactions in Jan 2025
    assert len(ret_matrix) >= 1
    jan_cohort = next((c for c in ret_matrix if c["cohort"] == "2025-01"), None)
    assert jan_cohort is not None
    assert jan_cohort["size"] == 3
    # Month 0 retention is always 100%
    assert jan_cohort["M+0"] == 100.0
    # Customer 1 & 2 transacted in Feb (M+1), Customer 3 did not -> 2/3 = 66.7%
    assert abs(jan_cohort["M+1"] - 66.7) < 0.2
    # Only Customer 1 transacted in March (M+2) -> 1/3 = 33.3%
    assert abs(jan_cohort["M+2"] - 33.3) < 0.2


def test_customer_segmentation_rules(db_session, seed_controlled_data):
    seg_engine = CustomerSegmentationEngine(db_session)
    res = seg_engine.compute_rfm_segments(as_of_date=datetime(2025, 3, 20))

    summary = {s["segment"]: s["customer_count"] for s in res["summary"]}
    assert res["total_evaluated"] == 3
    # High-Value Active: Customer 1 ($3000 spend, transacted March 10, recency = 10 days)
    assert summary.get("High-Value Active", 0) >= 1

import pytest
from datetime import datetime
from backend.app.analytics.metrics import BusinessMetricsEngine


def test_business_metrics_executive_summary(db_session, seed_controlled_data):
    """Verifies that SQL metrics match known controlled calculations exactly."""
    engine = BusinessMetricsEngine(db_session)
    summary = engine.get_executive_summary(
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 3, 31)
    )

    metrics = summary["metrics"]

    # Known controlled values:
    # TX-001 (1000) + TX-002 (1000) + TX-003 (1000) + TX-004 (200) + TX-005 (200) + TX-006 (100) = 3500.0
    # TX-007 is refunded (500), must be excluded.
    assert metrics["total_revenue"] == 3500.0
    # Total completed orders = 6 (excluding refund) or 7 total records
    assert metrics["transacting_customers"] == 3
    # AOV = 3500 / 6 = 583.33
    assert abs(metrics["average_order_value"] - 583.33) < 0.1


def test_revenue_breakdowns(db_session, seed_controlled_data):
    engine = BusinessMetricsEngine(db_session)
    breakdowns = engine.get_breakdowns()

    cats = {c["name"]: c["revenue"] for c in breakdowns["by_category"]}
    # SaaS: TX-001 (1000) + TX-002 (1000) + TX-003 (1000) + TX-006 (100) = 3100.0
    # Hardware: TX-004 (200) + TX-005 (200) = 400.0
    assert cats.get("SaaS") == 3100.0
    assert cats.get("Hardware") == 400.0


def test_pareto_concentration(db_session, seed_controlled_data):
    engine = BusinessMetricsEngine(db_session)
    pareto = engine.get_pareto_concentration()

    assert "concentration_points" in pareto
    assert len(pareto["concentration_points"]) > 0
    # Cumulative revenue must reach 100% at the end
    last_point = pareto["concentration_points"][-1]
    assert last_point["cumulative_revenue_pct"] == 100.0

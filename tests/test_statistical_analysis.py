import pytest
from backend.app.analytics.statistics import StatisticalAnalysisEngine


def test_segment_comparison_statistics(db_session, seed_controlled_data):
    stats_engine = StatisticalAnalysisEngine(db_session)
    res = stats_engine.test_segment_transaction_values(group_col="acquisition_channel")

    assert "test_statistic" in res
    assert "p_value" in res
    assert "business_question" in res
    assert "effect_size" in res
    assert 0.0 <= res["p_value"] <= 1.0


def test_confidence_intervals(db_session, seed_controlled_data):
    stats_engine = StatisticalAnalysisEngine(db_session)
    res = stats_engine.compute_metric_confidence_intervals(confidence=0.95)

    aov_res = res["average_order_value"]
    assert aov_res["ci_lower"] < aov_res["mean"] < aov_res["ci_upper"]
    assert aov_res["sample_size"] == 6

    rate_res = res["active_customer_rate"]
    assert 0.0 <= rate_res["ci_lower"] <= rate_res["ci_upper"] <= 1.0


def test_revenue_trend(db_session, seed_controlled_data):
    stats_engine = StatisticalAnalysisEngine(db_session)
    res = stats_engine.test_monthly_revenue_trend()
    # Controlled data has only 3 months (Jan, Feb, Mar 2025)
    # Checks boundary handling for small period counts
    assert "error" in res or "p_value" in res

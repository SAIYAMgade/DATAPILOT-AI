import pytest
from backend.app.insights import BusinessInsightEngine


def test_business_insights_generation(db_session, seed_controlled_data):
    engine = BusinessInsightEngine(db_session)
    insights = engine.generate_all_insights()

    assert isinstance(insights, list)
    for ins in insights:
        assert "title" in ins
        assert "category" in ins
        assert "metric_name" in ins
        assert "current_value" in ins
        assert "supporting_evidence" in ins
        assert "limitations" in ins
        assert ins["severity"] in ["info", "warning", "critical"]

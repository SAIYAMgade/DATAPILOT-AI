import pytest
from datetime import datetime, timedelta
from backend.app.ml.features import FeatureEngineeringService
from backend.app.models import Customer, Transaction, ProductCategory


def test_temporal_boundary_and_no_leakage(db_session):
    """
    Verifies that feature engineering strictly uses events on or before cutoff_date,
    and target strictly reflects events in the future prediction window.
    """
    cutoff = datetime(2025, 6, 1)
    obs_days = 90
    pred_days = 60

    cat = ProductCategory(code="CAT_A", name="Category A")
    db_session.add(cat)
    db_session.flush()

    # Customer 1: Has transactions before cutoff, and 1 transaction after cutoff in prediction window -> Retained (Target=0)
    c1 = Customer(customer_ref="LEAK-01", name="Cust 1", signup_date=datetime(2025, 1, 1))
    # Customer 2: Has transactions before cutoff, but ZERO after cutoff -> Churned (Target=1)
    c2 = Customer(customer_ref="LEAK-02", name="Cust 2", signup_date=datetime(2025, 1, 1))
    # Customer 3: Signed up AFTER cutoff -> Must be excluded from this cutoff cohort
    c3 = Customer(customer_ref="LEAK-03", name="Future Cust", signup_date=datetime(2025, 7, 1))

    db_session.add_all([c1, c2, c3])
    db_session.flush()

    txs = [
        # c1 before cutoff ($500)
        Transaction(transaction_ref="T1", customer_id=c1.id, category_id=cat.id, timestamp=cutoff - timedelta(days=20), amount=500.0, status="completed"),
        # c1 inside prediction window ($300) -> Must NOT be included in monetary_obs feature!
        Transaction(transaction_ref="T2", customer_id=c1.id, category_id=cat.id, timestamp=cutoff + timedelta(days=15), amount=300.0, status="completed"),
        # c2 before cutoff ($200)
        Transaction(transaction_ref="T3", customer_id=c2.id, category_id=cat.id, timestamp=cutoff - timedelta(days=40), amount=200.0, status="completed"),
        # c3 future tx
        Transaction(transaction_ref="T4", customer_id=c3.id, category_id=cat.id, timestamp=cutoff + timedelta(days=40), amount=100.0, status="completed"),
    ]
    db_session.add_all(txs)
    db_session.commit()

    service = FeatureEngineeringService(db_session)
    X, y = service.extract_features_and_target(cutoff_date=cutoff, observation_days=obs_days, prediction_days=pred_days)

    customer_ids = list(X["customer_id"])
    assert c1.id in customer_ids
    assert c2.id in customer_ids
    assert c3.id not in customer_ids  # Not eligible at cutoff

    # c1 features check: monetary_obs must be 500.0 (NOT 800.0)
    c1_row = X[X["customer_id"] == c1.id].iloc[0]
    assert c1_row["monetary_obs"] == 500.0
    assert c1_row["frequency_obs"] == 1

    # Target check: c1 has future tx -> target = 0 (not churned)
    c1_idx = X[X["customer_id"] == c1.id].index[0]
    assert y.iloc[c1_idx] == 0

    # Target check: c2 has no future tx -> target = 1 (churned)
    c2_idx = X[X["customer_id"] == c2.id].index[0]
    assert y.iloc[c2_idx] == 1

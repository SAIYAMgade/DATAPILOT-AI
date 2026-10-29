import pytest
from datetime import datetime
from backend.app.models import Customer, ProductCategory, Transaction


def test_customer_creation_and_constraints(db_session):
    cust = Customer(
        customer_ref="TEST-CUST-01",
        name="Test Corp",
        email="test@corp.com",
        signup_date=datetime(2025, 1, 1),
        is_active=True
    )
    db_session.add(cust)
    db_session.commit()

    saved = db_session.query(Customer).filter_by(customer_ref="TEST-CUST-01").first()
    assert saved is not None
    assert saved.name == "Test Corp"
    assert saved.email == "test@corp.com"
    assert saved.is_active is True


def test_transaction_foreign_key_relationship(db_session):
    cat = ProductCategory(code="CAT_TEST", name="Test Category")
    db_session.add(cat)
    db_session.flush()

    cust = Customer(
        customer_ref="TEST-CUST-02",
        name="Test Customer 2",
        signup_date=datetime(2025, 1, 1)
    )
    db_session.add(cust)
    db_session.flush()

    tx = Transaction(
        transaction_ref="TEST-TX-01",
        customer_id=cust.id,
        category_id=cat.id,
        timestamp=datetime(2025, 1, 5),
        amount=150.0,
        status="completed"
    )
    db_session.add(tx)
    db_session.commit()

    saved_tx = db_session.query(Transaction).filter_by(transaction_ref="TEST-TX-01").first()
    assert saved_tx is not None
    assert saved_tx.customer.name == "Test Customer 2"
    assert saved_tx.category.code == "CAT_TEST"
    assert saved_tx.amount == 150.0

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import Customer, ProductCategory, Transaction, CustomerActivity, DatasetBatch


@pytest.fixture(scope="session")
def test_engine():
    # Use SQLite in-memory or PostgreSQL test db
    test_db_url = settings.TEST_DATABASE_URL or "sqlite:///:memory:"
    connect_args = {"check_same_thread": False} if test_db_url.startswith("sqlite") else {}
    engine = create_engine(test_db_url, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionTest = sessionmaker(bind=connection)
    session = SessionTest()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_controlled_data(db_session):
    """Creates a deterministic, small dataset with known analytical properties for testing."""
    # 1. Product Categories
    cat1 = ProductCategory(code="CAT_SAAS", name="SaaS", description="Software")
    cat2 = ProductCategory(code="CAT_HW", name="Hardware", description="Hardware")
    db_session.add_all([cat1, cat2])
    db_session.flush()

    # 2. Customers
    # Customer 1: High value active
    c1 = Customer(
        customer_ref="CUST-001", name="Alpha Corp", email="a@alpha.com",
        segment="VIP", acquisition_channel="Direct Sales", region="North America",
        signup_date=datetime(2025, 1, 1), is_active=True
    )
    # Customer 2: Frequent active
    c2 = Customer(
        customer_ref="CUST-002", name="Beta LLC", email="b@beta.com",
        segment="Frequent", acquisition_channel="Organic", region="Europe",
        signup_date=datetime(2025, 1, 15), is_active=True
    )
    # Customer 3: Inactive / Churned (only transacted in Jan 2025)
    c3 = Customer(
        customer_ref="CUST-003", name="Gamma Inc", email="g@gamma.com",
        segment="Inactive", acquisition_channel="Partner Referral", region="North America",
        signup_date=datetime(2025, 1, 20), is_active=False
    )
    db_session.add_all([c1, c2, c3])
    db_session.flush()

    # 3. Transactions
    txs = [
        # Customer 1: 3 transactions, total $3000
        Transaction(transaction_ref="TX-001", customer_id=c1.id, category_id=cat1.id, timestamp=datetime(2025, 1, 10), amount=1000.0, status="completed"),
        Transaction(transaction_ref="TX-002", customer_id=c1.id, category_id=cat1.id, timestamp=datetime(2025, 2, 10), amount=1000.0, status="completed"),
        Transaction(transaction_ref="TX-003", customer_id=c1.id, category_id=cat1.id, timestamp=datetime(2025, 3, 10), amount=1000.0, status="completed"),

        # Customer 2: 2 transactions, total $400
        Transaction(transaction_ref="TX-004", customer_id=c2.id, category_id=cat2.id, timestamp=datetime(2025, 1, 25), amount=200.0, status="completed"),
        Transaction(transaction_ref="TX-005", customer_id=c2.id, category_id=cat2.id, timestamp=datetime(2025, 2, 25), amount=200.0, status="completed"),

        # Customer 3: 1 transaction in Jan only, total $100
        Transaction(transaction_ref="TX-006", customer_id=c3.id, category_id=cat1.id, timestamp=datetime(2025, 1, 22), amount=100.0, status="completed"),

        # 1 Refunded transaction: amount $500 (should be excluded from revenue)
        Transaction(transaction_ref="TX-007", customer_id=c1.id, category_id=cat1.id, timestamp=datetime(2025, 3, 15), amount=500.0, status="refunded", is_refund=True),
    ]
    db_session.add_all(txs)
    db_session.commit()

    return {
        "categories": [cat1, cat2],
        "customers": [c1, c2, c3],
        "transactions": txs
    }

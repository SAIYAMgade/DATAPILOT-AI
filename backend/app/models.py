from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, Text, JSON
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_ref = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    segment = Column(String(64), nullable=False, default="New")
    acquisition_channel = Column(String(64), nullable=False, default="Organic")
    region = Column(String(64), nullable=False, default="North America")
    signup_date = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    activities = relationship("CustomerActivity", back_populates="customer", cascade="all, delete-orphan")
    predictions = relationship("CustomerRiskPrediction", back_populates="customer", cascade="all, delete-orphan")


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(255), nullable=True)

    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_ref = Column(String(64), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, default="completed")  # completed, refunded, cancelled
    payment_method = Column(String(32), nullable=False, default="credit_card")
    is_refund = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="transactions")
    category = relationship("ProductCategory", back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_cust_time", "customer_id", "timestamp"),
        Index("ix_transactions_time_status", "timestamp", "status"),
    )


class CustomerActivity(Base):
    __tablename__ = "customer_activities"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type = Column(String(64), nullable=False)  # login, view_catalog, cart_update, support_ticket
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="activities")


class DatasetBatch(Base):
    __tablename__ = "dataset_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_ref = Column(String(64), unique=True, nullable=False, index=True)
    source_type = Column(String(32), nullable=False)  # synthetic, csv, json
    records_received = Column(Integer, default=0, nullable=False)
    records_accepted = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0, nullable=False)
    rejection_summary = Column(JSON, nullable=True)
    status = Column(String(32), default="pending", nullable=False)  # completed, failed, partial
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rejections = relationship("IngestionRejection", back_populates="batch", cascade="all, delete-orphan")


class IngestionRejection(Base):
    __tablename__ = "ingestion_rejections"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("dataset_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)
    raw_record = Column(Text, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    batch = relationship("DatasetBatch", back_populates="rejections")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_tag = Column(String(64), unique=True, nullable=False, index=True)
    model_type = Column(String(64), nullable=False)  # LogisticRegression, RandomForest, Baseline
    observation_days = Column(Integer, nullable=False, default=90)
    prediction_days = Column(Integer, nullable=False, default=60)
    feature_names = Column(JSON, nullable=False)
    threshold = Column(Float, nullable=False, default=0.5)
    metrics = Column(JSON, nullable=False)
    feature_importance = Column(JSON, nullable=True)
    artifact_path = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    predictions = relationship("CustomerRiskPrediction", back_populates="model_version")


class CustomerRiskPrediction(Base):
    __tablename__ = "customer_risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_category = Column(String(32), nullable=False)  # Low, Medium, High
    observation_end_date = Column(DateTime, nullable=False)
    prediction_horizon_days = Column(Integer, nullable=False, default=60)
    priority_score = Column(Float, nullable=False, default=0.0)
    contributing_features = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="predictions")
    model_version = relationship("ModelVersion", back_populates="predictions")

    __table_args__ = (
        Index("ix_pred_cust_date", "customer_id", "observation_end_date"),
    )


class BusinessInsight(Base):
    __tablename__ = "business_insights"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)  # revenue, retention, risk, operational
    metric_name = Column(String(64), nullable=False)
    comparison_period = Column(String(64), nullable=False)
    current_value = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)
    supporting_evidence = Column(JSON, nullable=False)
    limitations = Column(String(500), nullable=False)
    severity = Column(String(32), nullable=False, default="info")  # info, warning, critical
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
